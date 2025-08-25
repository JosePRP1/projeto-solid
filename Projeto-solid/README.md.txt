Projeto: Aplicação dos Princípios SOLID em um Sistema Bancário

Estrutura do Projeto

projeto-solid/
├── original/                 # Código original
│   └── OriginalClasses.py
├── solid/                   # Código refatorado com princípios SOLID
│   └── RefactoredClasses.py
└── README.md                # Documentação explicativa

---

Cliente

a) Classe Original
@dataclass(frozen=True)
class Cliente:
    id: int
    nome: str
    cpf: str

b) Princípio SOLID Aplicado
Nenhuma alteração necessária, pois a classe já respeita o SRP (Responsabilidade Única), modelando apenas os dados do cliente.

---

Conta

a) Classe Original
@dataclass
class Conta:
    numero: str
    cliente: Cliente
    saldo: Decimal = Decimal("0.00")
    historico: List[Transacao] = field(default_factory=list)

    def depositar(self, valor: Decimal, descricao: str = ""):
        ...

    def sacar(self, valor: Decimal, descricao: str = ""):
        ...

b) Princípio SOLID Aplicado
Princípio: SRP (Responsabilidade Única)

Explicação:
A classe Conta possuía múltiplas responsabilidades: além de gerenciar saldo, também era responsável por criar e registrar transações no histórico. Para respeitar o SRP, extraímos a responsabilidade do registro de transações para uma nova classe RegistroTransacoes.

c) Classe Refatorada
class RegistroTransacoes:
    def __init__(self):
        self._historico: List[Transacao] = []

    def registrar(self, transacao: Transacao):
        self._historico.append(transacao)

    def listar(self) -> List[Transacao]:
        return list(self._historico)

@dataclass
class Conta:
    numero: str
    cliente: Cliente
    saldo: Decimal = Decimal("0.00")
    transacoes: RegistroTransacoes = field(default_factory=RegistroTransacoes)

    def depositar(self, valor: Decimal, descricao: str = ""):
        ...

    def sacar(self, valor: Decimal, descricao: str = ""):
        ...

---

Banco

a) Classe Original
class Banco:
    def __init__(self):
        self._clientes_por_cpf: Dict[str, Cliente] = {}
        self._contas_por_numero: Dict[str, Conta] = {}
        self._seq_cliente = 1
        self._seq_conta = 1001
    ...

b) Princípios SOLID Aplicados

- OCP (Open/Closed Principle):
  A lógica de transferência foi encapsulada na classe Transferencia, permitindo estender operações futuras sem modificar Banco.

- DIP (Dependency Inversion Principle):
  O banco agora recebe as classes Cliente e Conta como dependências injetadas via construtor, aumentando a flexibilidade e testabilidade.

c) Classe Refatorada
class Banco:
    def __init__(self, cliente_cls=Cliente, conta_cls=Conta):
        self._clientes_por_cpf: Dict[str, Cliente] = {}
        self._contas_por_numero: Dict[str, Conta] = {}
        self._seq_cliente = 1
        self._seq_conta = 1001
        self._cliente_cls = cliente_cls
        self._conta_cls = conta_cls
    ...

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

---

Conclusão

Esta refatoração trouxe os seguintes benefícios:

- Separação clara de responsabilidades (SRP), facilitando manutenção e testes;
- Extensibilidade sem modificação do código existente (OCP);
- Flexibilidade na injeção de dependências (DIP), facilitando substituição e testes.

Esses princípios ajudam a tornar o sistema mais robusto, compreensível e adaptável a futuras mudanças.

---

Obrigado por acompanhar este projeto!
