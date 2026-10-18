
import os
import requests
import folium
from dotenv import load_dotenv



load_dotenv(".env")

TOKEN = os.getenv("SPTRANS_TOKEN")
NUMERO_LINHA = "8200-10"

BASE_URL = "http://api.olhovivo.sptrans.com.br/v2.1"


def solution():

    if not TOKEN:
        raise ValueError(
            "Token não encontrado! Verifique o arquivo .env."
        )

    s = requests.Session()

 

    print("Autenticando na SPTrans...")

    res = s.post(
        f"{BASE_URL}/Login/Autenticar",
        params={"token": TOKEN},
        timeout=30
    )
    res.raise_for_status()

    if res.text.strip().lower() != "true":
        raise RuntimeError("Falha na autenticação.")

    print("Autenticação realizada com sucesso!")

   
    print(f"Buscando a linha {NUMERO_LINHA}...")

    res = s.get(
        f"{BASE_URL}/Linha/Buscar",
        params={"termosBusca": NUMERO_LINHA},
        timeout=30
    )
    res.raise_for_status()

    linhas = res.json()

    
    linha = next(
        (
            item for item in linhas
            if f"{item.get('lt')}-{item.get('tl')}" == NUMERO_LINHA
        ),
        None
    )

    if linha is None:
        print("Não foi encontrada correspondência exata.")
        print("Linhas retornadas pela API:", linhas[:10])
        raise RuntimeError(
            f"Linha {NUMERO_LINHA} não encontrada."
        )

    codigo = linha["cl"]

    print("Linha encontrada!")
    print("Código comercial:", NUMERO_LINHA)
    print("Código interno:", codigo)

  
    print("Buscando as paradas...")

    res = s.get(
        f"{BASE_URL}/Parada/BuscarParadasPorLinha",
        params={"codigoLinha": codigo},
        timeout=30
    )
    res.raise_for_status()

    paradas = res.json()

    print("Quantidade de paradas:", len(paradas))
    print("Exemplo de parada:", paradas[:1])

  

    print("Buscando os ônibus em circulação...")

    res = s.get(
        f"{BASE_URL}/Posicao/Linha",
        params={"codigoLinha": codigo},
        timeout=30
    )
    res.raise_for_status()

    posicoes = res.json()
    onibus = posicoes.get("vs", [])

    print("Quantidade de ônibus retornados:", len(onibus))

  

    coordenadas = []

    for parada in paradas:
        lat = parada.get("py")
        lon = parada.get("px")

        if lat is not None and lon is not None:
            coordenadas.append([lat, lon])

    for veiculo in onibus:
        lat = veiculo.get("py")
        lon = veiculo.get("px")

        if lat is not None and lon is not None:
            coordenadas.append([lat, lon])

    if coordenadas:
        centro = [
            sum(p[0] for p in coordenadas) / len(coordenadas),
            sum(p[1] for p in coordenadas) / len(coordenadas)
        ]
    else:
        centro = [-23.5505, -46.6333]

    mapa = folium.Map(
        location=centro,
        zoom_start=13
    )

 

    print("Adicionando as paradas ao mapa...")

    paradas_adicionadas = 0

    for parada in paradas:

        lat = parada.get("py")
        lon = parada.get("px")

        if lat is None or lon is None:
            continue

        nome = parada.get("np", "Parada sem nome")
        endereco = parada.get("ed", "")

        folium.Marker(
            location=[lat, lon],
            popup=f"Parada: {nome}<br>Endereço: {endereco}",
            tooltip=f"Parada: {nome}",
            icon=folium.Icon(
                color="blue",
                icon="info-sign"
            )
        ).add_to(mapa)

        paradas_adicionadas += 1

  

    print("Adicionando os ônibus ao mapa...")

    onibus_adicionados = 0

    for veiculo in onibus:

        lat = veiculo.get("py")
        lon = veiculo.get("px")

        if lat is None or lon is None:
            continue

        prefixo = veiculo.get("p", "Não informado")
        horario = veiculo.get("ta", "Não informado")

        folium.Marker(
            location=[lat, lon],
            popup=(
                f"Ônibus: {prefixo}"
                f"<br>Última posição: {horario}"
            ),
            tooltip=f"Ônibus {prefixo}",
            icon=folium.Icon(
                color="red",
                icon="bus",
                prefix="fa"
            )
        ).add_to(mapa)

        onibus_adicionados += 1


    arquivo = "mapa_onibus.html"

    mapa.save(arquivo)




if __name__ == "__main__":
    solution()
