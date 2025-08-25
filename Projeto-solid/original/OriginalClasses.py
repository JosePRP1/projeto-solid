from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, getcontext
from datetime import datetime
from typing import Dict, List, Tuple

getcontext().prec = 28

class ErroBanco(Exception):
    pass

class ValorInvalido(ErroBanco):
    pass

class SaldoInsuficiente(ErroBanco):
    pass

class EntidadeNaoEncontrada(ErroBanco):
    pass

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

@dataclass
class Conta:
    numero: str
    cliente: Cliente
    saldo: Decimal = Decimal("0.00")
    historico: List[Transacao] = field(default_factory=list)

    def depositar(self, valor: Decimal, descricao: str = ""):
        if valor <= 0:
            raise ValorInvalido("valor deve ser positivo")
        self.saldo += valor
        self.historico.append(Transacao(datetime.utcnow(), "DEPOSITO", valor, descricao, destino=self.numero))

    def sacar(self, valor: Decimal, descricao: str = ""):
        if valor <= 0:
            raise ValorInvalido("valor deve ser positivo")
        if self.saldo < valor:
            raise SaldoInsuficiente("saldo insuficiente")
        self.saldo -= valor
        self.historico.append(Transacao(datetime.utcnow(), "SAQUE", valor, descricao, origem=self.numero))

class Banco:
    def __init__(self):
        self._clientes_por_cpf: Dict[str, Cliente] = {}
        self._contas_por_numero: Dict[str, Conta] = {}
        self._seq_cliente = 1
        self._seq_conta = 1001

    def criar_cliente(self, nome: str, cpf: str) -> Cliente:
        if cpf in self._clientes_por_cpf:
            return self._clientes_por_cpf[cpf]
        c = Cliente(self._seq_cliente, nome, cpf)
        self._clientes_por_cpf[cpf] = c
        self._seq_cliente += 1
        return c

    def abrir_conta(self, cpf: str) -> Conta:
        cliente = self._clientes_por_cpf.get(cpf)
        if not cliente:
            raise EntidadeNaoEncontrada("cliente não encontrado")
        numero = str(self._seq_conta)
        conta = Conta(numero, cliente)
        self._contas_por_numero[numero] = conta
        self._seq_conta += 1
        return conta

    def buscar_conta(self, numero: str) -> Conta:
        conta = self._contas_por_numero.get(numero)
        if not conta:
            raise EntidadeNaoEncontrada("conta não encontrada")
        return conta

    def depositar(self, numero: str, valor: Decimal):
        self.buscar_conta(numero).depositar(self._to_money(valor), "depósito")

    def sacar(self, numero: str, valor: Decimal):
        self.buscar_conta(numero).sacar(self._to_money(valor), "saque")

    def transferir(self, origem: str, destino: str, valor: Decimal):
        if origem == destino:
            raise ValorInvalido("contas iguais")
        v = self._to_money(valor)
        co = self.buscar_conta(origem)
        cd = self.buscar_conta(destino)
        co.sacar(v, f"transferência para {destino}")
        cd.depositar(v, f"transferência de {origem}")
        t = Transacao(datetime.utcnow(), "TRANSFERENCIA", v, "transferência", origem=origem, destino=destino)
        co.historico.append(t)
        cd.historico.append(t)

    def listar_clientes_e_contas(self) -> List[Tuple[Cliente, List[Conta]]]:
        m: Dict[str, List[Conta]] = {}
        for conta in self._contas_por_numero.values():
            m.setdefault(conta.cliente.cpf, []).append(conta)
        out = []
        for cpf, cliente in self._clientes_por_cpf.items():
            out.append((cliente, m.get(cpf, [])))
        return out

    def extrato(self, numero: str) -> List[Transacao]:
        return list(self.buscar_conta(numero).historico)

    def _to_money(self, valor) -> Decimal:
        if isinstance(valor, Decimal):
            v = valor
        else:
            try:
                v = Decimal(str(valor))
            except InvalidOperation:
                raise ValorInvalido("valor inválido")
        return v.quantize(Decimal("0.01"))

def criar_dados_mock() -> Banco:
    banco = Banco()
    a = banco.criar_cliente("Ana", "11111111111")
    b = banco.criar_cliente("Bruno", "22222222222")
    c = banco.criar_cliente("Carla", "33333333333")
    ca = banco.abrir_conta(a.cpf)
    cb = banco.abrir_conta(b.cpf)
    cc = banco.abrir_conta(c.cpf)
    banco.depositar(ca.numero, Decimal("1500"))
    banco.depositar(cb.numero, Decimal("800"))
    banco.depositar(cc.numero, Decimal("2500"))
    banco.transferir(cc.numero, ca.numero, Decimal("300"))
    banco.sacar(cb.numero, Decimal("100"))
    return banco

if __name__ == "__main__":
    banco = criar_dados_mock()
    for cliente, contas in banco.listar_clientes_e_contas():
        print(cliente.id, cliente.nome, cliente.cpf, "->", [(c.numero, f"{c.saldo:.2f}") for c in contas])
    n = next(iter({c.numero for _, cs in banco.listar_clientes_e_contas() for c in cs}))
    for t in banco.extrato(n):
        print(n, t.momento.isoformat(), t.tipo, f"{t.valor:.2f}", t.descricao)
