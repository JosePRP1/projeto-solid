# Refatoração com SRP, OCP e DIP

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, getcontext
from datetime import datetime
from typing import List, Dict, Protocol

getcontext().prec = 28

# --- EXCEÇÕES ---

class ErroBanco(Exception): pass
class ValorInvalido(ErroBanco): pass
class SaldoInsuficiente(ErroBanco): pass
class EntidadeNaoEncontrada(ErroBanco): pass

# --- MODELOS ---

@dataclass(frozen=True)
class Cliente:
    id: int
    nome: str
    cpf: str

@dataclass
class Transacao:
    momento: datetime
    tipo: str
    valor: Decimal
    descricao: str
    origem: str = ""
    destino: str = ""

# --- RESPONSABILIDADE ÚNICA: REGISTRO DE TRANSAÇÕES ---

class RegistroTransacoes:
    def __init__(self):
        self._historico: List[Transacao] = []

    def registrar(self, transacao: Transacao):
        self._historico.append(transacao)

    def listar(self) -> List[Transacao]:
        return list(self._historico)

# --- CONTA BANCÁRIA ---

@dataclass
class Conta:
    numero: str
    cliente: Cliente
    saldo: Decimal = Decimal("0.00")
    transacoes: RegistroTransacoes = field(default_factory=RegistroTransacoes)

    def depositar(self, valor: Decimal, descricao: str = ""):
        if valor <= 0:
            raise ValorInvalido("valor deve ser positivo")
        self.saldo += valor
        self.transacoes.registrar(Transacao(datetime.utcnow(), "DEPOSITO", valor, descricao, destino=self.numero))

    def sacar(self, valor: Decimal, descricao: str = ""):
        if valor <= 0:
            raise ValorInvalido("valor deve ser positivo")
        if self.saldo < valor:
            raise SaldoInsuficiente("saldo insuficiente")
        self.saldo -= valor
        self.transacoes.registrar(Transacao(datetime.utcnow(), "SAQUE", valor, descricao, origem=self.numero))

# --- ABSTRAÇÃO PARA OPERAÇÕES (OCP) ---

class Operacao(Protocol):
    def executar(self): pass

@dataclass
class Transferencia:
    origem: Conta
    destino: Conta
    valor: Decimal

    def executar(self):
        if self.origem.numero == self.destino.numero:
            raise ValorInvalido("contas iguais")
        self.origem.sacar(self.valor, f"Transferência para {self.destino.numero}")
        self.destino.depositar(self.valor, f"Transferência de {self.origem.numero}")
        transacao = Transacao(datetime.utcnow(), "TRANSFERENCIA", self.valor, "Transferência",
                              origem=self.origem.numero, destino=self.destino.numero)
        self.origem.transacoes.registrar(transacao)
        self.destino.transacoes.registrar(transacao)

# --- BANCO (DIP: usando dependências via construtor) ---

class Banco:
    def __init__(self, cliente_cls=Cliente, conta_cls=Conta):
        self._clientes_por_cpf: Dict[str, Cliente] = {}
        self._contas_por_numero: Dict[str, Conta] = {}
        self._seq_cliente = 1
        self._seq_conta = 1001
        self._cliente_cls = cliente_cls
        self._conta_cls = conta_cls

    def criar_cliente(self, nome: str, cpf: str) -> Cliente:
        if cpf in self._clientes_por_cpf:
            return self._clientes_por_cpf[cpf]
        c = self._cliente_cls(self._seq_cliente, nome, cpf)
        self._clientes_por_cpf[cpf] = c
        self._seq_cliente += 1
        return c

    def abrir_conta(self, cpf: str) -> Conta:
        cliente = self._clientes_por_cpf.get(cpf)
        if not cliente:
            raise EntidadeNaoEncontrada("cliente não encontrado")
        numero = str(self._seq_conta)
        conta = self._conta_cls(numero, cliente)
        self._contas_por_numero[numero] = conta
        self._seq_conta += 1
        return conta

    def buscar_conta(self, numero: str) -> Conta:
        conta = self._contas_por_numero.get(numero)
        if not conta:
            raise EntidadeNaoEncontrada("conta não encontrada")
        return conta

    def depositar(self, numero: str, valor):
        self.buscar_conta(numero).depositar(self._to_money(valor), "Depósito")

    def sacar(self, numero: str, valor):
        self.buscar_conta(numero).sacar(self._to_money(valor), "Saque")

    def transferir(self, origem: str, destino: str, valor):
        op = Transferencia(self.buscar_conta(origem), self.buscar_conta(destino), self._to_money(valor))
        op.executar()

    def extrato(self, numero: str) -> List[Transacao]:
        return self.buscar_conta(numero).transacoes.listar()

    def listar_clientes_e_contas(self):
        m: Dict[str, List[Conta]] = {}
        for conta in self._contas_por_numero.values():
            m.setdefault(conta.cliente.cpf, []).append(conta)
        return [(cliente, m.get(cliente.cpf, [])) for cliente in self._clientes_por_cpf.values()]

    def _to_money(self, valor) -> Decimal:
        try:
            return Decimal(str(valor)).quantize(Decimal("0.01"))
        except InvalidOperation:
            raise ValorInvalido("valor inválido")
