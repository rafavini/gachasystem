
import random
from collections import Counter

# ==================================================
# CONFIGURACOES
# ==================================================


SALDO_INICIAL = 0

CUSTO_PULL_COMUM = 500
CUSTO_PULL_PREMIUM = 800

# o custo dos pulls pagos sobe conforme o total de cartas do jogador:
# custo = base * (1 + AUMENTO_CUSTO_POR_CARTA * total_de_cartas)
AUMENTO_CUSTO_POR_CARTA = 0.01

LIMITE_GRATIS_DIARIO = 4

# seguranca contra loop infinito de compras no mesmo dia
MAX_COMPRAS_DIA = 10

# chance (por dia) de o jogador esperar juntar moedas pro premium
# em vez de gastar logo num pull comum
PROB_ESPERAR_PREMIUM = 0.5

# inicial quando se registra 
BONUS_PULLS_GRATIS = 5 
BONUS_PULLS_COMUM = 10

TOTAL_ESTRELAS = 10
FATOR_RARIDADE = 0.5
FATOR_ACABAMENTO = 0.28

TOTAL_CARTAS = 10000

cartas = [
    f"Carta {i}" for i in range(1, TOTAL_CARTAS + 1)
]


# ==================================================
# RECOMPENSAS DAS ESTRELAS
# ==================================================

def gerar_recompensas():

    recompensas = {}
    valor = 1

    for estrela in range(1, TOTAL_ESTRELAS + 1):

        recompensas[estrela] = valor
        valor = valor * 2 + 1

    return recompensas


RECOMPENSAS = gerar_recompensas()


# ==================================================
# ACABAMENTOS E MULTIPLICADORES
# ==================================================

ACABAMENTOS = {
    "Normal": 1.0,
    "Foil": 1.5,
    "Neon": 2.0,
    "Full Art": 3.0,
    "Prismatico": 4.0,
    "Estilhacado": 6.0,
    "Signature": 10.0
}


# ==================================================
# GERAR PROBABILIDADES
# ==================================================

def gerar_probabilidades(limite, fator):

    pesos = [
        fator ** i
        for i in range(limite)
    ]

    total = sum(pesos)

    return [
        peso / total
        for peso in pesos
    ]


# ==================================================
# SORTEAR ESTRELAS
# ==================================================

def sortear_estrela(limite_estrelas):

    probabilidades = gerar_probabilidades(
        limite_estrelas,
        FATOR_RARIDADE
    )

    return random.choices(
        range(1, limite_estrelas + 1),
        weights=probabilidades,
        k=1
    )[0]


# ==================================================
# SORTEAR ACABAMENTO
# ==================================================

def sortear_acabamento():

    nomes = list(ACABAMENTOS.keys())

    probabilidades = gerar_probabilidades(
        len(nomes),
        FATOR_ACABAMENTO
    )

    return random.choices(
        nomes,
        weights=probabilidades,
        k=1
    )[0]


# ==================================================
# REALIZAR PULL
# ==================================================

def realizar_pull(quantidade, limite_estrelas):

    cartas_sorteadas = random.sample(
        cartas,
        quantidade
    )

    resultados = []

    for carta in cartas_sorteadas:

        # Primeiro sorteia as estrelas
        estrela = sortear_estrela(limite_estrelas)

        # Depois sorteia o acabamento
        acabamento = sortear_acabamento()

        # Calcula a renda
        renda_base = RECOMPENSAS[estrela]

        multiplicador = ACABAMENTOS[acabamento]

        renda_final = renda_base * multiplicador

        resultados.append({
            "carta": carta,
            "estrelas": estrela,
            "acabamento": acabamento,
            "multiplicador": multiplicador,
            "renda_base": renda_base,
            "renda": renda_final
        })

    return resultados


# ==================================================
# TIPOS DE PULL
# ==================================================

def pull_gratis():
    return realizar_pull(3, 4)


def pull_comum():
    return realizar_pull(5, 4)


def pull_premium():
    return realizar_pull(3, 10)


# ==================================================
# EXECUTAR PULL E ATUALIZAR SALDO
# ==================================================

def custo_pull(tipo, estatisticas=None):

    if tipo == "comum":
        base = CUSTO_PULL_COMUM
    elif tipo == "premium":
        base = CUSTO_PULL_PREMIUM
    else:
        return 0

    total_cartas = (
        sum(estatisticas["estrelas"].values()) if estatisticas else 0
    )

    return round(base * (1 + AUMENTO_CUSTO_POR_CARTA * total_cartas))


def executar_pull(tipo, saldo, estatisticas=None, sem_custo=False):

    if tipo == "gratis":

        custo = 0
        resultados = pull_gratis()

    elif tipo == "comum":

        custo = custo_pull("comum", estatisticas)
        resultados = pull_comum()

    elif tipo == "premium":

        custo = custo_pull("premium", estatisticas)
        resultados = pull_premium()

    else:

        print("Tipo de pull invalido!")
        return saldo, 0

    # Pulls de bonus nao descontam moedas
    if sem_custo:
        custo = 0

    if saldo < custo:

        print("Saldo insuficiente!")
        return saldo, 0

    saldo -= custo

    # A renda das cartas NAO entra na hora: ela e acumulada pelo
    # inventario e resgatada uma vez por dia (ver simular_dia)
    renda_adicionada = sum(
        item["renda"] for item in resultados
    )

    if estatisticas is not None:
        if custo > 0:
            estatisticas["compras"][tipo] += 1
            estatisticas["gasto"][tipo] += custo
        for item in resultados:
            estatisticas["estrelas"][item["estrelas"]] += 1
            estatisticas["acabamentos"][item["acabamento"]] += 1
            estatisticas["combinacoes"][
                (item["estrelas"], item["acabamento"])
            ] += 1

    print("\n" + "=" * 55)
    print(f"PULL {tipo.upper()}")
    print("=" * 55)

    for item in resultados:

        print(
            f'{item["carta"]} | '
            f'{item["estrelas"]} estrelas | '
            f'{item["acabamento"]} | '
            f'{item["multiplicador"]}x | '
            f'{item["renda"]:.2f} moedas/dia'
        )

    print("-" * 55)

    print(f"Custo: {custo:.2f}")
    print(f"Renda diaria adicionada: +{renda_adicionada:.2f}")
    print(f"Saldo atual: {saldo:.2f}")

    return saldo, renda_adicionada


# ==================================================
# RENDA DIARIA DO INVENTARIO
# ==================================================

def renda_por_dia(estatisticas):
    # "combinacoes" guarda quantas copias de cada (estrela, acabamento)
    # o jogador possui; cada copia rende sua renda todo dia.
    return sum(
        qtd * RECOMPENSAS[estrela] * ACABAMENTOS[acabamento]
        for (estrela, acabamento), qtd in estatisticas["combinacoes"].items()
    )


# ==================================================
# BONUS DE ENTRADA
# ==================================================

def bonus_de_entrada(saldo, estatisticas=None):

    print("\n========== BONUS DE ENTRADA ==========")
    print(
        f"Voce ganhou {BONUS_PULLS_GRATIS} pulls gratis e "
        f"{BONUS_PULLS_COMUM} pulls comuns!"
    )

    renda_bonus = 0

    for _ in range(BONUS_PULLS_GRATIS):

        saldo, renda = executar_pull(
            "gratis", saldo, estatisticas, sem_custo=True
        )
        renda_bonus += renda

    for _ in range(BONUS_PULLS_COMUM):

        saldo, renda = executar_pull(
            "comum", saldo, estatisticas, sem_custo=True
        )
        renda_bonus += renda

    print("\nRENDA DIARIA DO BONUS:", round(renda_bonus, 2))
    print("SALDO:", round(saldo, 2))

    return saldo, renda_bonus


# ==================================================
# SIMULAR UM DIA
# ==================================================

def simular_dia(dia, saldo, estatisticas):

    print(f"\n========== DIA {dia} ==========")

    # Resgata a renda acumulada pelas cartas que ja possui
    recompensa_diaria = renda_por_dia(estatisticas)
    saldo += recompensa_diaria

    print(f"Renda resgatada das cartas: +{recompensa_diaria:.2f}")

    for pull in range(1, LIMITE_GRATIS_DIARIO + 1):

        saldo, _ = executar_pull(
            "gratis",
            saldo,
            estatisticas
        )

    # Gasta o saldo comprando pulls (premium primeiro, depois comum)
    gasto_dia = 0
    compras_dia = 0

    while compras_dia < MAX_COMPRAS_DIA:

        custo_premium = custo_pull("premium", estatisticas)
        custo_comum = custo_pull("comum", estatisticas)

        if saldo >= custo_premium:
            tipo, custo = "premium", custo_premium
        elif saldo >= custo_comum:
            # Jogador pode esperar juntar moedas para o premium
            if random.random() < PROB_ESPERAR_PREMIUM:
                break
            tipo, custo = "comum", custo_comum
        else:
            break

        saldo, _ = executar_pull(tipo, saldo, estatisticas)

        gasto_dia += custo
        compras_dia += 1

    print("\nRESGATE DO DIA:", round(recompensa_diaria, 2))
    print("GASTO DO DIA:", gasto_dia)
    print("RENDA DIARIA ATUAL:", round(renda_por_dia(estatisticas), 2))
    print("SALDO:", round(saldo, 2))

    return saldo, recompensa_diaria, gasto_dia


# ==================================================
# SIMULAR VARIOS DIAS
# ==================================================

def simular_dias():

    saldo = SALDO_INICIAL

    dias = int(input("Quantos dias deseja simular? "))

    historico = []

    estatisticas = {
        "estrelas": Counter(),
        "acabamentos": Counter(),
        "combinacoes": Counter(),
        "compras": Counter(),
        "gasto": Counter()
    }

    saldo, recompensa_bonus = bonus_de_entrada(saldo, estatisticas)

    for dia in range(1, dias + 1):

        saldo, recompensa, gasto = simular_dia(dia, saldo, estatisticas)

        historico.append({
            "dia": dia,
            "recompensa": recompensa,
            "gasto": gasto,
            "saldo": saldo
        })

    print("\n========== RELATORIO FINAL ==========")

    for registro in historico:

        print(
            f"Dia {registro['dia']} | "
            f"Gerado: {registro['recompensa']:.2f} | "
            f"Gasto: {registro['gasto']:.2f} | "
            f"Saldo: {registro['saldo']:.2f}"
        )

    total_gerado = sum(
        item["recompensa"] for item in historico
    )

    print(f"\nBonus de entrada: +{recompensa_bonus:.2f} de renda/dia")
    print(f"RENDA DIARIA FINAL: {renda_por_dia(estatisticas):.2f}")
    print("SALDO INICIAL:", SALDO_INICIAL)
    print("SALDO FINAL:", round(saldo, 2))
    print("TOTAL DE MOEDAS GERADAS:", round(total_gerado, 2))
    print("TOTAL GASTO:", sum(estatisticas["gasto"].values()))
    print("PULLS PREMIUM COMPRADOS:", estatisticas["compras"]["premium"])
    print("PULLS COMUNS COMPRADOS:", estatisticas["compras"]["comum"])

    exibir_resumo_cartas(estatisticas)


# ==================================================
# RESUMO DE CARTAS OBTIDAS
# ==================================================

def exibir_resumo_cartas(estatisticas):

    total = sum(estatisticas["estrelas"].values())

    print("\n========== CARTAS OBTIDAS ==========")
    print("TOTAL DE CARTAS:", total)

    print("\nPor estrela:")
    for estrela in range(1, TOTAL_ESTRELAS + 1):
        qtd = estatisticas["estrelas"][estrela]
        if qtd:
            print(f"  {estrela} estrela(s): {qtd}")

    print("\nPor acabamento:")
    for nome in ACABAMENTOS:
        print(f"  {nome}: {estatisticas['acabamentos'][nome]}")

    print("\nPor estrela x acabamento:")
    for estrela in range(1, TOTAL_ESTRELAS + 1):
        if not estatisticas["estrelas"][estrela]:
            continue
        partes = [
            f"{nome}={estatisticas['combinacoes'][(estrela, nome)]}"
            for nome in ACABAMENTOS
        ]
        print(f"  {estrela} estrela(s): " + " | ".join(partes))


# ==================================================
# EXECUCAO
# ==================================================

if __name__ == "__main__":

    simular_dias()
