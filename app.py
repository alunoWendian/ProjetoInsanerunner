import math
import random
import sqlite3
import sys
import pygame


# ==========================================
# 1. BANCO DE DADOS (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            pontos INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def salvar_pontuacao(nome, pontos):
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO placar (nome, pontos) VALUES (?, ?)', (nome, pontos)
    )
    conn.commit()
    conn.close()


# ==========================================
# 2. CONFIGURAÇÕES DO JOGO
# ==========================================
pygame.init()
init_db()

LARGURA, ALTURA = 320, 180
LARGURA_TELA, ALTURA_TELA = 800, 600

tela_interna = pygame.Surface((LARGURA, ALTURA))
janela = pygame.display.set_mode(
    (LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE | pygame.SCALED
)
pygame.display.set_caption('Insane Runner')

relogio = pygame.time.Clock()

# Cores
PRETO = (10, 10, 12)
DESTRUICAO_PRETO = (5, 5, 8)
ROXO_CAOS = (140, 20, 220)
ROXO_ESCURO = (60, 10, 100)
CINZA_JOGADOR = (160, 160, 160)
CINZA_PEDRA = (100, 100, 110)
CINZA_PEDRA_GRANDE = (70, 70, 80)
CINZA_PEDRA_DESLIZE = (130, 130, 150)
BRANCO = (255, 255, 255)
VERMELHO = (230, 40, 40)
AMARELO = (240, 220, 40)
VERDE_GRADE = (50, 200, 100)
ROSA_LOVERS = (240, 80, 160)
ROSA_ESCURO = (150, 30, 90)
COR_COXINHA = (215, 135, 45)
CINZA_SERRA = (180, 185, 195)
VERDE_PRAGA = (30, 150, 60)
VERMELHO_OLHO = (255, 20, 20)
VERMELHO_MINA = (200, 50, 30)
MARROM_REVENGER = (130, 65, 25)
AZUL_SOBREVIVENTE = (70, 130, 180)

# ==========================================
# 3. LINHAS E VARIÁVEIS DO JOGO
# ==========================================
LINHAS_Y = [70, 105, 140]
linha_atual = 1

player_offset_x = 100
player_largura = 12
player_altura_normal = 24
player_altura_deslize = 10

pulo = False
altura_pulo = 0
vel_pulo = 0
gravidade = 0.55
deslizando = False
boost_deslize = 0.0

debuff_movimento_timer = 0
tempo_invencivel = 0
DURACAO_IFRAMES = 60

chao_offset = 0

velocidade_base = 2.5
velocidade_jogo = velocidade_base
aceleracao_por_frame = 0.0006
velocidade_maxima = 5.0

obstaculos = []
coxinhas = []
tempo_proximo_obstaculo = 0
tempo_proxima_coxinha = 0

tropecos = 0
alcance_destruicao_atual = 12.0
pulso_caos = 0
animando_consumo = False

pontos = 0
acumulador_pontos = 0.0

PRIMEIRO_GATILHO = 500
INTERVALO_MODIFICADOR = 1000
proximo_gatilho_pontos = PRIMEIRO_GATILHO

game_over = False
# O ESTADO INICIAL AGORA É 'MENU'
estado_jogo = 'MENU'

TODOS_MODIFICADORES = [
    'DISPARADOR',
    'LOVERS.EXE',
    'ROBERT',
    'O MESTRE',
    'BARRA AMALDIÇOADA',
    'AFIADA',
    'LAS PRAGAS',
    'CARANGUEJO MINA',
    'REVENGER',
    'SOBREVIVENTES',
]
modificadores_ativos = set()

opcoes_grade = ['DISPARADOR', 'LOVERS.EXE', 'ROBERT']
grade_x = LARGURA + 20

robert_ativo = False
las_pragas_ativo = False
caranguejo_mina_ativo = False
revenger_ativo = False
sobreviventes_ativo = False

sobreviventes = []
tempo_proximo_sobrevivente = 0

revenger_estado = 'DESATIVADO'
revenger_timer = 0
revenger_x = 0
revenger_y = 0
revenger_linha_alvo = 0
revenger_rastro = []
revenger_tempo_flutuando = 0
revenger_deslizando = False
revenger_angulo = 0.0
revenger_alvo_x = 0
revenger_alvo_y = 0

disparador_ativo = False
mira_x, mira_y = 0, 0
temporizador_disparo = 0
estado_disparo = 'DESATIVADO'
tempo_piscada = 0
angulo_mira = 0

lovers_ativa = False
lovers_x, lovers_y = 0, 0
lovers_vel_x = 0
lovers_vel_y = 0
lovers_alvo_x = 0
lovers_alvo_y = 0
estado_lovers = 'DESATIVADO'
timer_lovers = 0
lovers_alpha = 0
lovers_ja_acertou = False

mestre_ativo = False
mestre_timer = 200
mestre_ordem_ativa = False
mestre_estado = 'AGUARDANDO'
mestre_timer_alerta = 0
mestre_texto = ''
mestre_acao_requerida = None
mestre_eh_valido = False
mestre_tempo_restante = 0
mestre_cumpriu_acao = False

FRASES_MESTRE = [
    {'texto': 'O Mestre mandou pular!', 'acao': 'PULAR', 'valido': True},
    {'texto': 'O Mestre mandou deslizar!', 'acao': 'DESLIZAR', 'valido': True},
    {
        'texto': 'O Mestre mandou mudar de linha!',
        'acao': 'MOVER',
        'valido': True,
    },
    {'texto': 'Mude de Linha!', 'acao': 'MOVER', 'valido': False},
    {'texto': 'Pule!', 'acao': 'PULAR', 'valido': False},
    {'texto': 'Deslize!', 'acao': 'DESLIZAR', 'valido': False},
]

barra_amaldicoada_ativa = False
barra_amaldicoada_nivel = 0.0
barra_amaldicoada_velocidade = 0.08

afiadas = []
timer_proxima_afiada = 0


def reiniciar_todas_variaveis():
    global game_over, animando_consumo, tropecos, tempo_invencivel, debuff_movimento_timer
    global alcance_destruicao_atual, pontos, acumulador_pontos, proximo_gatilho_pontos
    global velocidade_jogo, player_offset_x, linha_atual, tempo_proximo_obstaculo
    global tempo_proxima_coxinha, tempo_proximo_sobrevivente, timer_proxima_afiada
    global boost_deslize, disparador_ativo, estado_disparo, angulo_mira, lovers_ativa
    global estado_lovers, robert_ativo, las_pragas_ativo, caranguejo_mina_ativo
    global revenger_ativo, sobreviventes_ativo, revenger_estado, revenger_angulo
    global mestre_ativo, mestre_ordem_ativa, mestre_estado, barra_amaldicoada_ativa
    global barra_amaldicoada_nivel

    game_over = False
    animando_consumo = False
    tropecos = 0
    tempo_invencivel = 0
    debuff_movimento_timer = 0
    alcance_destruicao_atual = 12.0
    pontos = 0
    acumulador_pontos = 0.0
    proximo_gatilho_pontos = PRIMEIRO_GATILHO
    velocidade_jogo = velocidade_base
    player_offset_x = 100
    linha_atual = 1
    obstaculos.clear()
    coxinhas.clear()
    afiadas.clear()
    sobreviventes.clear()
    modificadores_ativos.clear()
    tempo_proximo_obstaculo = 0
    tempo_proxima_coxinha = 0
    tempo_proximo_sobrevivente = 0
    timer_proxima_afiada = 0
    boost_deslize = 0.0

    disparador_ativo = False
    estado_disparo = 'DESATIVADO'
    angulo_mira = 0
    lovers_ativa = False
    estado_lovers = 'DESATIVADO'
    robert_ativo = False
    las_pragas_ativo = False
    caranguejo_mina_ativo = False
    revenger_ativo = False
    sobreviventes_ativo = False
    revenger_estado = 'DESATIVADO'
    revenger_rastro.clear()
    revenger_angulo = 0.0

    mestre_ativo = False
    mestre_ordem_ativa = False
    mestre_estado = 'AGUARDANDO'

    barra_amaldicoada_ativa = False
    barra_amaldicoada_nivel = 0.0


def tomar_dano():
    global tropecos, animando_consumo, tempo_invencivel
    if tempo_invencivel <= 0:
        tropecos += 1
        tempo_invencivel = DURACAO_IFRAMES
        if tropecos >= 3:
            animando_consumo = True


def linha_destinada_segura(linha_origem, lista_obs, pos_x):
    linhas_possiveis = [l for l in [0, 1, 2] if l != linha_origem]
    for obs in lista_obs:
        if obs['linha'] in linhas_possiveis:
            if abs(obs['x'] - pos_x) < 45:
                return False
    return True


# ==========================================
# 4. LOOP PRINCIPAL
# ==========================================
while True:
    relogio.tick(60)
    teclas = pygame.key.get_pressed()

    acao_jogador_frame = None

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if evento.type == pygame.KEYDOWN:
            if estado_jogo == 'MENU':
                if evento.key == pygame.K_SPACE or evento.key == pygame.K_RETURN:
                    reiniciar_todas_variaveis()
                    estado_jogo = 'CORRIDA'
            elif not game_over:
                if (
                    evento.key == pygame.K_UP or evento.key == pygame.K_w
                ) and linha_atual > 0:
                    linha_atual -= 1
                    acao_jogador_frame = 'MOVER'
                if (
                    (evento.key == pygame.K_DOWN or evento.key == pygame.K_s)
                    and linha_atual < 2
                    and not deslizando
                ):
                    linha_atual += 1
                    acao_jogador_frame = 'MOVER'

                if (
                    evento.key == pygame.K_SPACE
                    and not pulo
                    and not deslizando
                    and debuff_movimento_timer <= 0
                ):
                    pulo = True
                    vel_pulo = -5.5
                    acao_jogador_frame = 'PULAR'
            else:
                if evento.key == pygame.K_r:
                    estado_jogo = 'MENU'

    if estado_jogo != 'MENU' and not game_over:
        chao_offset = (chao_offset + velocidade_jogo) % 20

        if tempo_invencivel > 0:
            tempo_invencivel -= 1

        if debuff_movimento_timer > 0:
            debuff_movimento_timer -= 1

        y_base_player = LINHAS_Y[linha_atual]

        if (
            (
                teclas[pygame.K_LSHIFT]
                or teclas[pygame.K_RSHIFT]
                or teclas[pygame.K_c]
            )
            and not pulo
            and debuff_movimento_timer <= 0
        ):
            if not deslizando:
                acao_jogador_frame = 'DESLIZAR'
                boost_deslize = 2.8
            deslizando = True
        else:
            deslizando = False
            boost_deslize = 0.0

        if deslizando:
            player_offset_x += boost_deslize
            boost_deslize = max(0.0, boost_deslize - 0.15)

        h_player = player_altura_deslize if deslizando else player_altura_normal
        y_player = y_base_player - h_player + int(altura_pulo)
        rect_player = pygame.Rect(
            player_offset_x, y_player, player_largura, h_player
        )

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            player_offset_x -= 1.8
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            player_offset_x += 1.8

        player_offset_x = max(20, min(LARGURA - 30, player_offset_x))

        if pulo:
            altura_pulo += vel_pulo
            vel_pulo += gravidade
            if altura_pulo >= 0:
                altura_pulo = 0
                pulo = False

        # BARRA AMALDIÇOADA
        if barra_amaldicoada_ativa and not animando_consumo:
            barra_amaldicoada_nivel += barra_amaldicoada_velocidade

            if barra_amaldicoada_nivel >= 100.0:
                barra_amaldicoada_nivel = 100.0
                animando_consumo = True

            tempo_proxima_coxinha -= 1
            if tempo_proxima_coxinha <= 0:
                linha_coxinha = random.randint(0, 2)
                coxinhas.append({
                    'x': LARGURA + 10,
                    'linha': linha_coxinha,
                    'largura': 8,
                    'altura': 8,
                })
                tempo_proxima_coxinha = random.randint(150, 300)

        # CORRIDA
        if estado_jogo == 'CORRIDA':
            if velocidade_jogo < velocidade_maxima:
                velocidade_jogo += aceleracao_por_frame

            acumulador_pontos += 0.5
            pontos = int(acumulador_pontos)

            if pontos >= proximo_gatilho_pontos:
                disponiveis = [
                    m
                    for m in TODOS_MODIFICADORES
                    if m not in modificadores_ativos
                ]

                if len(disponiveis) < 3:
                    disponiveis = TODOS_MODIFICADORES

                estado_jogo = 'SELECAO'
                grade_x = LARGURA + 20
                opcoes_grade = random.sample(disponiveis, 3)
                proximo_gatilho_pontos += INTERVALO_MODIFICADOR

            tempo_proximo_obstaculo -= 1
            if tempo_proximo_obstaculo <= 0 and not animando_consumo:
                if caranguejo_mina_ativo and random.random() < 0.15:
                    for l in range(3):
                        obstaculos.append({
                            'tipo': 'caranguejo_mina',
                            'x': LARGURA + 10,
                            'linha': l,
                            'y_atual': float(LINHAS_Y[l]),
                            'offset_y': 0,
                            'largura': 16,
                            'altura': 8,
                            'is_robert': False,
                            'trocou_linha': False,
                        })
                else:
                    tipo = random.choice(
                        ['pedra_normal', 'pedra_grande', 'pedra_deslize']
                    )

                    if las_pragas_ativo and tipo == 'pedra_normal':
                        tipo = 'las_pragas'

                    linha_sorteada = random.randint(0, 2)
                    eh_robert = (
                        robert_ativo
                        and (tipo != 'las_pragas')
                        and (random.random() < 0.35)
                    )
                    y_inicial = LINHAS_Y[linha_sorteada]

                    dados_obs = {
                        'tipo': tipo,
                        'x': LARGURA + 10,
                        'linha': linha_sorteada,
                        'y_atual': float(y_inicial),
                        'offset_y': 0,
                        'is_robert': eh_robert,
                        'trocou_linha': False,
                    }

                    if tipo == 'pedra_normal' or tipo == 'las_pragas':
                        dados_obs.update({'largura': 14, 'altura': 10})
                    elif tipo == 'pedra_grande':
                        dados_obs.update({'largura': 16, 'altura': 50})
                    elif tipo == 'pedra_deslize':
                        dados_obs.update(
                            {'largura': 14, 'altura': 40, 'offset_y': 11}
                        )

                    obstaculos.append(dados_obs)

                intervalo_min = int(60 / (velocidade_jogo / 2.5))
                intervalo_max = int(110 / (velocidade_jogo / 2.5))
                tempo_proximo_obstaculo = random.randint(
                    max(30, intervalo_min), max(60, intervalo_max)
                )

        # SELEÇÃO
        elif estado_jogo == 'SELECAO':
            grade_x -= 1.2

            if grade_x <= player_offset_x + player_largura:
                escolha = opcoes_grade[linha_atual]
                modificadores_ativos.add(escolha)

                if escolha == 'DISPARADOR':
                    disparador_ativo = True
                    temporizador_disparo = 100
                elif escolha == 'LOVERS.EXE':
                    lovers_ativa = True
                    timer_lovers = 60
                    estado_lovers = 'DESATIVADO'
                elif escolha == 'ROBERT':
                    robert_ativo = True
                elif escolha == 'O MESTRE':
                    mestre_ativo = True
                    mestre_timer = 180
                elif escolha == 'BARRA AMALDIÇOADA':
                    barra_amaldicoada_ativa = True
                    tempo_proxima_coxinha = 60
                elif escolha == 'AFIADA':
                    vx = random.choice([-0.9, 0.9])
                    vy = random.choice([-0.7, 0.7])
                    afiadas.append({
                        'x': float(random.randint(50, LARGURA - 50)),
                        'y': float(random.randint(20, ALTURA - 40)),
                        'vel_x': vx,
                        'vel_y': vy,
                        'raio': 14,
                    })
                elif escolha == 'LAS PRAGAS':
                    las_pragas_ativo = True
                elif escolha == 'CARANGUEJO MINA':
                    caranguejo_mina_ativo = True
                elif escolha == 'REVENGER':
                    revenger_ativo = True
                    revenger_estado = 'FLUTUANDO'
                    revenger_x = LARGURA + 20
                    revenger_y = 30
                    revenger_timer = 120
                elif escolha == 'SOBREVIVENTES':
                    sobreviventes_ativo = True
                    tempo_proximo_sobrevivente = 30

                velocidade_jogo = velocidade_base
                estado_jogo = 'CORRIDA'

        # SOBREVIVENTES LOGIC & SPAWN (LINHAS ADJACENTES E SUAVES)
        if sobreviventes_ativo and not animando_consumo:
            tempo_proximo_sobrevivente -= 1
            if tempo_proximo_sobrevivente <= 0:
                linha_iniciar = random.randint(0, 2)
                sobreviventes.append({
                    'x': -25.0,
                    'linha': linha_iniciar,
                    'y_atual': float(LINHAS_Y[linha_iniciar]),
                    'pulo': False,
                    'altura_pulo': 0.0,
                    'vel_pulo': 0.0,
                    'deslizando': False,
                    'timer_deslize': 0,
                    'vel_propria': random.uniform(0.6, 1.1),
                    'cd_troca_linha': 0,
                })
                tempo_proximo_sobrevivente = random.randint(220, 380)

            for sob in sobreviventes[:]:
                sob['x'] += sob['vel_propria']

                y_alvo = LINHAS_Y[sob['linha']]
                sob['y_atual'] += (y_alvo - sob['y_atual']) * 0.2

                if sob['cd_troca_linha'] > 0:
                    sob['cd_troca_linha'] -= 1

                if sob['pulo']:
                    sob['altura_pulo'] += sob['vel_pulo']
                    sob['vel_pulo'] += gravidade
                    if sob['altura_pulo'] >= 0:
                        sob['altura_pulo'] = 0.0
                        sob['pulo'] = False

                if sob['deslizando']:
                    sob['timer_deslize'] -= 1
                    if sob['timer_deslize'] <= 0:
                        sob['deslizando'] = False

                sensor_rect = pygame.Rect(
                    sob['x'] + 12, sob['y_atual'] - 24, 45, 24
                )
                for obs in obstaculos:
                    if obs['linha'] == sob['linha']:
                        obs_rect = pygame.Rect(
                            obs['x'],
                            LINHAS_Y[obs['linha']] - obs['altura'],
                            obs['largura'],
                            obs['altura'],
                        )
                        if sensor_rect.colliderect(obs_rect):
                            if obs['tipo'] in [
                                'pedra_normal',
                                'las_pragas',
                                'caranguejo_mina',
                            ]:
                                if not sob['pulo'] and not sob['deslizando']:
                                    sob['pulo'] = True
                                    sob['vel_pulo'] = -5.5
                            elif obs['tipo'] == 'pedra_deslize':
                                if not sob['pulo']:
                                    sob['deslizando'] = True
                                    sob['timer_deslize'] = 25
                            elif obs['tipo'] == 'pedra_grande':
                                if sob['cd_troca_linha'] <= 0:
                                    if sob['linha'] == 0:
                                        sob['linha'] = 1
                                    elif sob['linha'] == 2:
                                        sob['linha'] = 1
                                    elif sob['linha'] == 1:
                                        sob['linha'] = random.choice([0, 2])

                                    sob['cd_troca_linha'] = 50

                h_sob = (
                    player_altura_deslize
                    if sob['deslizando']
                    else player_altura_normal
                )
                y_sob = sob['y_atual'] - h_sob + int(sob['altura_pulo'])
                rect_sob = pygame.Rect(sob['x'], y_sob, player_largura, h_sob)

                if sob['linha'] == linha_atual and rect_player.colliderect(
                    rect_sob
                ):
                    debuff_movimento_timer = 150

                if sob['x'] > LARGURA + 30:
                    sobreviventes.remove(sob)

        # COXINHAS
        for coxinha in coxinhas[:]:
            coxinha['x'] -= velocidade_jogo

            if coxinha['linha'] == linha_atual:
                y_coxinha = (
                    LINHAS_Y[coxinha['linha']] - coxinha['altura'] - 4
                )
                rect_coxinha = pygame.Rect(
                    coxinha['x'],
                    y_coxinha,
                    coxinha['largura'],
                    coxinha['altura'],
                )

                if rect_player.colliderect(rect_coxinha):
                    barra_amaldicoada_nivel = max(
                        0.0, barra_amaldicoada_nivel - 35.0
                    )
                    coxinhas.remove(coxinha)
                    continue

            if coxinha['x'] < -20:
                coxinhas.remove(coxinha)

        # OBSTÁCULOS
        for obs in obstaculos[:]:
            obs['x'] -= velocidade_jogo

            y_alvo = LINHAS_Y[obs['linha']]
            obs['y_atual'] += (y_alvo - obs['y_atual']) * 0.15

            if (
                obs.get('is_robert')
                and not obs['trocou_linha']
                and not animando_consumo
            ):
                if 70 < (obs['x'] - player_offset_x) < 130:
                    if obs['linha'] != linha_atual:
                        if obs['linha'] < linha_atual:
                            obs['linha'] += 1
                        else:
                            obs['linha'] -= 1
                        obs['trocou_linha'] = True

            if obs['linha'] == linha_atual and not animando_consumo:
                y_visivel_base = obs['y_atual'] - obs['offset_y']

                if obs['tipo'] == 'pedra_deslize':
                    y_obs = y_visivel_base - 18
                    h_colisao = 18
                else:
                    y_obs = y_visivel_base - obs['altura']
                    h_colisao = obs['altura']

                rect_obs = pygame.Rect(
                    obs['x'], y_obs, obs['largura'], h_colisao
                )

                if rect_player.colliderect(rect_obs):
                    if obs['tipo'] == 'las_pragas':
                        animando_consumo = True
                    else:
                        tomar_dano()

                    if obs['tipo'] == 'caranguejo_mina':
                        x_mina = obs['x']
                        obstaculos = [
                            o
                            for o in obstaculos
                            if not (
                                o['tipo'] == 'caranguejo_mina'
                                and abs(o['x'] - x_mina) < 5
                            )
                        ]
                    else:
                        obstaculos.remove(obs)
                    continue

            if obs['x'] < -20:
                if obs in obstaculos:
                    obstaculos.remove(obs)

        # REVENGER
        if revenger_ativo and not animando_consumo:
            revenger_tempo_flutuando += 0.1

            h_revenger = (
                player_altura_deslize
                if revenger_deslizando
                else player_altura_normal
            )
            w_revenger = player_largura

            revenger_rastro.append(
                (revenger_x, revenger_y, revenger_deslizando, revenger_angulo)
            )
            if len(revenger_rastro) > 5:
                revenger_rastro.pop(0)

            if revenger_estado == 'FLUTUANDO':
                revenger_deslizando = False
                revenger_angulo = 0.0
                revenger_x += (LARGURA - 40 - revenger_x) * 0.05
                revenger_y = 25 + math.sin(revenger_tempo_flutuando) * 12

                revenger_timer -= 1
                if revenger_timer <= 0:
                    revenger_estado = 'ALERTA'
                    revenger_linha_alvo = random.randint(0, 2)
                    revenger_timer = 40

            elif revenger_estado == 'ALERTA':
                revenger_deslizando = False
                y_alvo = LINHAS_Y[revenger_linha_alvo] - player_altura_normal
                revenger_y += (y_alvo - revenger_y) * 0.2

                revenger_timer -= 1
                if revenger_timer <= 0:
                    revenger_estado = 'RECUO_ANTECIPACAO'
                    revenger_alvo_x = revenger_x + 30.0
                    revenger_timer = 18

            elif revenger_estado == 'RECUO_ANTECIPACAO':
                revenger_x += (revenger_alvo_x - revenger_x) * 0.25
                revenger_timer -= 1
                if revenger_timer <= 0:
                    revenger_estado = 'INVESTIDA'

            elif revenger_estado == 'INVESTIDA':
                revenger_deslizando = True
                revenger_y = (
                    LINHAS_Y[revenger_linha_alvo] - player_altura_deslize
                )
                revenger_x -= 11.0

                rect_revenger = pygame.Rect(
                    revenger_x, revenger_y, w_revenger, h_revenger
                )

                if rect_player.colliderect(rect_revenger):
                    if deslizando:
                        revenger_estado = 'REBATIDO'
                        revenger_alvo_x = revenger_x + 90.0
                        revenger_timer = 25
                        revenger_angulo = 0.0
                    else:
                        tomar_dano()

                if revenger_x < -40:
                    revenger_estado = 'RETORNANDO'
                    revenger_alvo_x = LARGURA - 40
                    revenger_alvo_y = 25

            elif revenger_estado == 'REBATIDO':
                revenger_deslizando = False
                progresso_giro = (25 - revenger_timer) / 25.0
                revenger_angulo = -360.0 * progresso_giro
                revenger_x += (revenger_alvo_x - revenger_x) * 0.25

                revenger_timer -= 1
                if revenger_timer <= 0:
                    revenger_angulo = 0.0
                    revenger_estado = 'RETORNANDO'
                    revenger_alvo_x = LARGURA - 40
                    revenger_alvo_y = 25

            elif revenger_estado == 'RETORNANDO':
                revenger_deslizando = False
                revenger_angulo = 0.0
                revenger_x += (revenger_alvo_x - revenger_x) * 0.08
                revenger_y += (revenger_alvo_y - revenger_y) * 0.08

                if (
                    abs(revenger_x - revenger_alvo_x) < 5
                    and abs(revenger_y - revenger_alvo_y) < 5
                ):
                    revenger_estado = 'FLUTUANDO'
                    revenger_timer = random.randint(180, 300)

        # AFIADA
        for afiada in afiadas:
            if not animando_consumo:
                afiada['x'] += afiada['vel_x']
                afiada['y'] += afiada['vel_y']

                r = afiada['raio']

                if afiada['x'] - r <= 0:
                    afiada['x'] = r
                    afiada['vel_x'] *= -1
                elif afiada['x'] + r >= LARGURA:
                    afiada['x'] = LARGURA - r
                    afiada['vel_x'] *= -1

                if afiada['y'] - r <= 0:
                    afiada['y'] = r
                    afiada['vel_y'] *= -1
                elif afiada['y'] + r >= ALTURA:
                    afiada['y'] = ALTURA - r
                    afiada['vel_y'] *= -1

                rect_afiada = pygame.Rect(
                    afiada['x'] - r, afiada['y'] - r, r * 2, r * 2
                )
                if rect_player.colliderect(rect_afiada):
                    tomar_dano()

        # O MESTRE
        if mestre_ativo and not animando_consumo:
            if not mestre_ordem_ativa:
                mestre_timer -= 1
                if mestre_timer <= 0:
                    candidatas = FRASES_MESTRE.copy()
                    if not linha_destinada_segura(
                        linha_atual, obstaculos, player_offset_x
                    ):
                        candidatas = [
                            f for f in candidatas if f['acao'] != 'MOVER'
                        ]

                    ordem_sorteada = random.choice(candidatas)
                    mestre_texto = ordem_sorteada['texto']
                    mestre_acao_requerida = ordem_sorteada['acao']
                    mestre_eh_valido = ordem_sorteada['valido']
                    mestre_estado = 'ALERTA'
                    mestre_timer_alerta = 35
                    mestre_cumpriu_acao = False
                    mestre_ordem_ativa = True
            else:
                if mestre_estado == 'ALERTA':
                    mestre_timer_alerta -= 1
                    if mestre_timer_alerta <= 0:
                        mestre_estado = 'ATIVO'
                        mestre_tempo_restante = 150

                elif mestre_estado == 'ATIVO':
                    mestre_tempo_restante -= 1

                    if acao_jogador_frame == mestre_acao_requerida:
                        if mestre_eh_valido:
                            mestre_cumpriu_acao = True
                        else:
                            tomar_dano()
                            mestre_ordem_ativa = False
                            mestre_timer = random.randint(350, 550)

                    if mestre_tempo_restante <= 0:
                        if mestre_eh_valido and not mestre_cumpriu_acao:
                            tomar_dano()

                        mestre_ordem_ativa = False
                        mestre_timer = random.randint(350, 550)

        # DISPARADOR
        if disparador_ativo and not animando_consumo:
            temporizador_disparo -= 1

            if estado_disparo == 'DESATIVADO':
                if temporizador_disparo <= 0:
                    estado_disparo = 'SEGUINDO'
                    temporizador_disparo = 90

            elif estado_disparo == 'SEGUINDO':
                mira_x += (rect_player.centerx - mira_x) * 0.12
                mira_y += (rect_player.centery - mira_y) * 0.12
                angulo_mira = (angulo_mira + 8) % 360

                if temporizador_disparo <= 0:
                    estado_disparo = 'TRAVADO_PISCANDO'
                    temporizador_disparo = 35
                    tempo_piscada = 0
                    angulo_mira = 0

            elif estado_disparo == 'TRAVADO_PISCANDO':
                tempo_piscada += 1
                if temporizador_disparo <= 0:
                    estado_disparo = 'ATIRANDO'

            elif estado_disparo == 'ATIRANDO':
                rect_mira = pygame.Rect(mira_x - 9, mira_y - 9, 18, 18)
                if rect_player.colliderect(rect_mira):
                    tomar_dano()

                estado_disparo = 'DESATIVADO'
                temporizador_disparo = random.randint(120, 220)

        # LOVERS.EXE
        if lovers_ativa and not animando_consumo:
            timer_lovers -= 1

            if estado_lovers == 'DESATIVADO':
                if timer_lovers <= 0:
                    estado_lovers = 'FADE_IN'
                    lovers_alpha = 0
                    lovers_x = random.randint(LARGURA - 40, LARGURA - 10)
                    lovers_y = random.randint(10, ALTURA - 30)
                    lovers_ja_acertou = False
                    timer_lovers = 40

            elif estado_lovers == 'FADE_IN':
                lovers_alpha = min(255, lovers_alpha + 8)
                if timer_lovers <= 0:
                    estado_lovers = 'CORACAO_INTEIRO'
                    timer_lovers = 35

            elif estado_lovers == 'CORACAO_INTEIRO':
                if timer_lovers <= 0:
                    estado_lovers = 'CORACAO_RACHADO'
                    timer_lovers = 25

                    lovers_alvo_x = rect_player.centerx - 12
                    lovers_alvo_y = rect_player.centery - 12

                    dx = lovers_alvo_x - lovers_x
                    dy = lovers_alvo_y - lovers_y

                    distancia = ((dx**2) + (dy**2)) ** 0.5
                    if distancia == 0:
                        distancia = 1

                    velocidade_dash = 7.5
                    lovers_vel_x = (dx / distancia) * velocidade_dash
                    lovers_vel_y = (dy / distancia) * velocidade_dash

            elif estado_lovers == 'CORACAO_RACHADO':
                if timer_lovers <= 0:
                    estado_lovers = 'RASANTE'

            elif estado_lovers == 'RASANTE':
                lovers_x += lovers_vel_x
                lovers_y += lovers_vel_y

                rect_lovers = pygame.Rect(lovers_x, lovers_y, 24, 24)

                if (
                    rect_player.colliderect(rect_lovers)
                    and not lovers_ja_acertou
                ):
                    tomar_dano()
                    lovers_ja_acertou = True

                if (
                    lovers_x < -40
                    or lovers_x > LARGURA + 40
                    or lovers_y < -40
                    or lovers_y > ALTURA + 40
                ):
                    estado_lovers = 'DESATIVADO'
                    timer_lovers = random.randint(140, 240)

        # CAOS LOGIC
        if not animando_consumo:
            alvo_destruicao = 12 + (tropecos * 35)
            alcance_destruicao_atual += (
                alvo_destruicao - alcance_destruicao_atual
            ) * 0.08
        else:
            alcance_destruicao_atual += 5
            if alcance_destruicao_atual >= LARGURA:
                game_over = True
                salvar_pontuacao('Visitante Feira', pontos)

        pulso_caos = (pulso_caos + 0.12) % 8

    # ==========================================
    # 5. RENDERIZAÇÃO
    # ==========================================
    tela_interna.fill(PRETO)

    if estado_jogo == 'MENU':
        # --- RENDERIZAÇÃO TELA DE MENU ---
        for y in LINHAS_Y:
            pygame.draw.line(
                tela_interna, (20, 20, 30), (0, y), (LARGURA, y), 1
            )

        fonte_titulo = pygame.font.SysFont(None, 26, bold=True)
        fonte_sub = pygame.font.SysFont(None, 14)
        fonte_info = pygame.font.SysFont(None, 12)

        txt_titulo = fonte_titulo.render('INSANE RUNNER', True, ROXO_CAOS)
        txt_sub = fonte_sub.render(
            'PRESSIONE ESPAÇO PARA COMECAR', True, BRANCO
        )

        txt_ctrl1 = fonte_info.render(
            'W/S ou SETAS : Trocar Linha', True, CINZA_JOGADOR
        )
        txt_ctrl2 = fonte_info.render('ESPAÇO : Pular', True, CINZA_JOGADOR)
        txt_ctrl3 = fonte_info.render(
            'SHIFT / C : Deslizar', True, CINZA_JOGADOR
        )

        tela_interna.blit(
            txt_titulo, (LARGURA // 2 - txt_titulo.get_width() // 2, 35)
        )

        # Efeito piscante no texto de início
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            tela_interna.blit(
                txt_sub, (LARGURA // 2 - txt_sub.get_width() // 2, 75)
            )

        tela_interna.blit(
            txt_ctrl1, (LARGURA // 2 - txt_ctrl1.get_width() // 2, 115)
        )
        tela_interna.blit(
            txt_ctrl2, (LARGURA // 2 - txt_ctrl2.get_width() // 2, 130)
        )
        tela_interna.blit(
            txt_ctrl3, (LARGURA // 2 - txt_ctrl3.get_width() // 2, 145)
        )

    else:
        # --- RENDERIZAÇÃO DO JOGO (CORRIDA / SELEÇÃO) ---
        limite_caos = alcance_destruicao_atual + pulso_caos

        # CAMADA 0: Pistas
        for y in LINHAS_Y:
            pygame.draw.line(
                tela_interna, (30, 30, 40), (0, y), (LARGURA, y), 1
            )
            for x in range(-20 + int(-chao_offset), LARGURA + 20, 20):
                pygame.draw.line(
                    tela_interna, (50, 50, 65), (x, y), (x + 8, y), 1
                )

        # Alerta de linha Revenger
        if (
            revenger_estado in ['ALERTA', 'RECUO_ANTECIPACAO']
            and not animando_consumo
        ):
            y_aviso = LINHAS_Y[revenger_linha_alvo] - 12
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                pygame.draw.rect(
                    tela_interna, (100, 30, 10), (0, y_aviso, LARGURA, 12)
                )

        # CAMADA 1: O Caos
        largura_visivel = int(limite_caos)
        if largura_visivel > 0:
            pygame.draw.rect(
                tela_interna, DESTRUICAO_PRETO, (0, 0, largura_visivel, ALTURA)
            )
            pygame.draw.line(
                tela_interna,
                ROXO_CAOS,
                (largura_visivel, 0),
                (largura_visivel, ALTURA),
                2,
            )
            for i in range(0, ALTURA, 12):
                offset_fogo = (int(pulso_caos) + i) % 7
                pygame.draw.rect(
                    tela_interna,
                    ROXO_ESCURO,
                    (largura_visivel - 6 + offset_fogo, i, 4, 6),
                )

        # CAMADA 2: Entidades
        if not game_over and not animando_consumo:
            # Coxinhas
            for coxinha in coxinhas:
                y_coxinha = LINHAS_Y[coxinha['linha']] - coxinha['altura'] - 4
                cor_c = (
                    ROXO_CAOS if coxinha['x'] <= limite_caos else COR_COXINHA
                )
                pygame.draw.polygon(
                    tela_interna,
                    cor_c,
                    [
                        (coxinha['x'] + 4, y_coxinha),
                        (coxinha['x'], y_coxinha + 8),
                        (coxinha['x'] + 8, y_coxinha + 8),
                    ],
                )

            # Sobreviventes
            for sob in sobreviventes:
                h_sob = (
                    player_altura_deslize
                    if sob['deslizando']
                    else player_altura_normal
                )
                y_sob = sob['y_atual'] - h_sob + int(sob['altura_pulo'])
                rect_sob = pygame.Rect(sob['x'], y_sob, player_largura, h_sob)

                if sob['x'] <= limite_caos:
                    cor_sob = ROXO_CAOS
                    pygame.draw.rect(tela_interna, cor_sob, rect_sob)
                    pygame.draw.rect(tela_interna, BRANCO, rect_sob, 1)
                else:
                    cor_sob = AZUL_SOBREVIVENTE
                    pygame.draw.rect(tela_interna, cor_sob, rect_sob)

            # Disparador
            if disparador_ativo:
                cor_disp = (
                    ROXO_CAOS if (LARGURA - 25) <= limite_caos else (80, 20, 30)
                )
                pygame.draw.rect(
                    tela_interna, cor_disp, (LARGURA - 25, 25, 12, 18)
                )
                pygame.draw.circle(
                    tela_interna, VERMELHO, (LARGURA - 19, 30), 3
                )

            # Obstáculos
            for obs in obstaculos:
                y_visivel_base = obs['y_atual'] - obs['offset_y']
                no_caos = obs['x'] <= limite_caos

                if obs['tipo'] == 'las_pragas':
                    y_obs = y_visivel_base - obs['altura']
                    rect_praga = pygame.Rect(
                        obs['x'], y_obs, obs['largura'], obs['altura']
                    )
                    cor_borda = ROXO_CAOS if no_caos else BRANCO
                    pygame.draw.rect(
                        tela_interna, cor_borda, rect_praga.inflate(2, 2), 1
                    )
                    pygame.draw.rect(tela_interna, DESTRUICAO_PRETO, rect_praga)

                    for i in range(3):
                        ox = obs['x'] + 2 + (i * 4) + random.randint(-1, 1)
                        oy = y_obs + 3 + random.randint(-1, 1)
                        cor_olho_p = ROXO_CAOS if no_caos else VERMELHO_OLHO
                        tela_interna.set_at((int(ox), int(oy)), cor_olho_p)

                elif obs['tipo'] == 'caranguejo_mina':
                    y_obs = y_visivel_base - obs['altura']
                    cor_mina = ROXO_CAOS if no_caos else VERMELHO_MINA
                    pygame.draw.rect(
                        tela_interna,
                        cor_mina,
                        (obs['x'], y_obs, obs['largura'], obs['altura']),
                    )
                    pygame.draw.line(
                        tela_interna,
                        BRANCO,
                        (obs['x'] - 2, y_obs + 2),
                        (obs['x'], y_obs + 4),
                        1,
                    )
                    pygame.draw.line(
                        tela_interna,
                        BRANCO,
                        (obs['x'] + obs['largura'], y_obs + 4),
                        (obs['x'] + obs['largura'] + 2, y_obs + 2),
                        1,
                    )
                    if (pygame.time.get_ticks() // 150) % 2 == 0:
                        pygame.draw.circle(
                            tela_interna,
                            AMARELO,
                            (
                                int(obs['x'] + obs['largura'] // 2),
                                int(y_obs + 2),
                            ),
                            2,
                        )

                elif obs['tipo'] == 'pedra_deslize':
                    y_obs = y_visivel_base - 18
                    cor_desl = ROXO_CAOS if no_caos else CINZA_PEDRA_DESLIZE
                    pygame.draw.rect(
                        tela_interna,
                        cor_desl,
                        (obs['x'], y_obs, obs['largura'], 18),
                    )
                else:
                    y_obs = y_visivel_base - obs['altura']
                    cor_p = (
                        ROXO_CAOS
                        if no_caos
                        else (
                            CINZA_PEDRA_GRANDE
                            if obs['tipo'] == 'pedra_grande'
                            else CINZA_PEDRA
                        )
                    )
                    pygame.draw.rect(
                        tela_interna,
                        cor_p,
                        (obs['x'], y_obs, obs['largura'], obs['altura']),
                    )

                if obs.get('is_robert'):
                    post_it_x = obs['x'] + 2
                    post_it_y = y_obs + 2
                    pygame.draw.rect(
                        tela_interna, AMARELO, (post_it_x, post_it_y, 7, 7)
                    )
                    tela_interna.set_at(
                        (int(post_it_x + 1), int(post_it_y + 1)), PRETO
                    )
                    tela_interna.set_at(
                        (int(post_it_x + 5), int(post_it_y + 1)), PRETO
                    )
                    tela_interna.set_at(
                        (int(post_it_x + 1), int(post_it_y + 4)), PRETO
                    )
                    tela_interna.set_at(
                        (int(post_it_x + 3), int(post_it_y + 5)), PRETO
                    )
                    tela_interna.set_at(
                        (int(post_it_x + 5), int(post_it_y + 4)), PRETO
                    )

            # Revenger
            if revenger_estado in [
                'FLUTUANDO',
                'ALERTA',
                'RECUO_ANTECIPACAO',
                'INVESTIDA',
                'REBATIDO',
                'RETORNANDO',
            ]:
                h_rev_atual = (
                    player_altura_deslize
                    if revenger_deslizando
                    else player_altura_normal
                )
                no_caos_revenger = revenger_x <= limite_caos
                cor_base_revenger = (
                    ROXO_CAOS if no_caos_revenger else MARROM_REVENGER
                )

                for idx, item in enumerate(revenger_rastro):
                    rx, ry, r_deslize, r_ang = (
                        item[0],
                        item[1],
                        item[2],
                        item[3],
                    )
                    h_rastro = (
                        player_altura_deslize
                        if r_deslize
                        else player_altura_normal
                    )
                    transparencia = (idx + 1) * 35

                    surf_rastro_base = pygame.Surface(
                        (player_largura, h_rastro), pygame.SRCALPHA
                    )
                    surf_rastro_base.fill((*cor_base_revenger, transparencia))

                    if r_ang != 0.0:
                        surf_rastro_rot = pygame.transform.rotate(
                            surf_rastro_base, r_ang
                        )
                        rect_rastro = surf_rastro_rot.get_rect(
                            center=(
                                int(rx + player_largura // 2),
                                int(ry + h_rastro // 2),
                            )
                        )
                        tela_interna.blit(surf_rastro_rot, rect_rastro)
                    else:
                        tela_interna.blit(surf_rastro_base, (rx, ry))

                surf_revenger = pygame.Surface(
                    (player_largura, h_rev_atual), pygame.SRCALPHA
                )
                surf_revenger.fill(cor_base_revenger)
                pygame.draw.rect(surf_revenger, AMARELO, (2, 3, 3, 3))

                if revenger_angulo != 0.0:
                    surf_rotacionada = pygame.transform.rotate(
                        surf_revenger, revenger_angulo
                    )
                    rect_rot = surf_rotacionada.get_rect(
                        center=(
                            int(revenger_x + player_largura // 2),
                            int(revenger_y + h_rev_atual // 2),
                        )
                    )
                    tela_interna.blit(surf_rotacionada, rect_rot)
                else:
                    tela_interna.blit(surf_revenger, (revenger_x, revenger_y))

            # Jogador
            if tempo_invencivel == 0 or (tempo_invencivel // 4) % 2 == 0:
                no_caos_player = player_offset_x <= limite_caos
                cor_player = ROXO_CAOS if no_caos_player else CINZA_JOGADOR

                if debuff_movimento_timer > 0:
                    cor_player = AMARELO

                pygame.draw.rect(tela_interna, cor_player, rect_player)

                if no_caos_player:
                    pygame.draw.rect(tela_interna, BRANCO, rect_player, 1)

            # Afiada
            for afiada in afiadas:
                cx, cy = int(afiada['x']), int(afiada['y'])
                r = afiada['raio']

                no_caos = cx <= limite_caos
                cor_serra = ROXO_CAOS if no_caos else CINZA_SERRA
                cor_olho = ROXO_CAOS if no_caos else VERMELHO

                pygame.draw.circle(tela_interna, cor_serra, (cx, cy), r)
                pygame.draw.line(
                    tela_interna,
                    cor_serra,
                    (cx - r - 3, cy),
                    (cx + r + 3, cy),
                    1,
                )
                pygame.draw.line(
                    tela_interna,
                    cor_serra,
                    (cx, cy - r - 3),
                    (cx, cy + r + 3),
                    1,
                )
                pygame.draw.line(
                    tela_interna,
                    cor_serra,
                    (cx - r + 3, cy - r + 3),
                    (cx + r - 3, cy + r - 3),
                    1,
                )
                pygame.draw.line(
                    tela_interna,
                    cor_serra,
                    (cx - r + 3, cy + r - 3),
                    (cx + r - 3, cy - r + 3),
                    1,
                )
                pygame.draw.circle(tela_interna, PRETO, (cx, cy), 6)
                pygame.draw.circle(tela_interna, cor_olho, (cx, cy), 3)

            # Lovers.exe
            if estado_lovers in [
                'FADE_IN',
                'CORACAO_INTEIRO',
                'CORACAO_RACHADO',
                'RASANTE',
            ]:
                if estado_lovers == 'CORACAO_RACHADO':
                    pygame.draw.aaline(
                        tela_interna,
                        ROSA_ESCURO,
                        (lovers_x + 12, lovers_y + 12),
                        (lovers_alvo_x + 12, lovers_alvo_y + 12),
                    )

                surf_lovers = pygame.Surface((32, 32), pygame.SRCALPHA)
                alpha_atual = lovers_alpha if estado_lovers == 'FADE_IN' else 255

                no_caos_lovers = lovers_x <= limite_caos
                cor_lovers_base = (
                    ROSA_LOVERS if not no_caos_lovers else ROXO_CAOS
                )

                pygame.draw.rect(
                    surf_lovers, (*ROSA_ESCURO, alpha_atual), (0, 0, 7, 7)
                )
                pygame.draw.rect(
                    surf_lovers, (*ROSA_ESCURO, alpha_atual), (25, 0, 7, 7)
                )
                pygame.draw.rect(
                    surf_lovers, (*ROSA_ESCURO, alpha_atual), (0, 25, 7, 7)
                )
                pygame.draw.rect(
                    surf_lovers, (*ROSA_ESCURO, alpha_atual), (25, 25, 7, 7)
                )

                pygame.draw.rect(
                    surf_lovers,
                    (*cor_lovers_base, alpha_atual),
                    (4, 4, 24, 24),
                    2,
                )
                pygame.draw.rect(
                    surf_lovers, (*PRETO, alpha_atual), (6, 6, 20, 20)
                )

                if estado_lovers == 'CORACAO_INTEIRO':
                    pygame.draw.rect(
                        surf_lovers, (*VERMELHO, alpha_atual), (12, 12, 8, 8)
                    )
                elif estado_lovers == 'CORACAO_RACHADO':
                    pygame.draw.rect(
                        surf_lovers, (*VERMELHO, alpha_atual), (12, 12, 8, 8)
                    )
                    pygame.draw.line(
                        surf_lovers,
                        (*AMARELO, alpha_atual),
                        (15, 10),
                        (16, 18),
                        1,
                    )
                elif estado_lovers == 'RASANTE':
                    pygame.draw.rect(
                        surf_lovers, (*BRANCO, alpha_atual), (11, 11, 10, 10)
                    )

                tela_interna.blit(surf_lovers, (lovers_x - 4, lovers_y - 4))

        # CAMADA 3: Overlays / Interface
        if estado_jogo == 'SELECAO' and not animando_consumo:
            pygame.draw.rect(
                tela_interna, VERDE_GRADE, (grade_x, 30, 6, 130), 2
            )
            fonte_m = pygame.font.SysFont(None, 12)

            for i, y_linha in enumerate(LINHAS_Y):
                pygame.draw.line(
                    tela_interna,
                    VERDE_GRADE,
                    (grade_x, y_linha - 20),
                    (grade_x + 60, y_linha - 20),
                    1,
                )
                txt_mod = fonte_m.render(opcoes_grade[i], True, BRANCO)
                tela_interna.blit(txt_mod, (grade_x + 8, y_linha - 15))

        if (
            estado_disparo in ['SEGUINDO', 'TRAVADO_PISCANDO', 'ATIRANDO']
            and not animando_consumo
        ):
            cor_mira = VERMELHO
            if estado_disparo == 'TRAVADO_PISCANDO':
                cor_mira = (
                    AMARELO if (tempo_piscada // 4) % 2 == 0 else VERMELHO
                )
            elif estado_disparo == 'ATIRANDO':
                cor_mira = BRANCO

            if mira_x <= limite_caos and estado_disparo != 'TRAVADO_PISCANDO':
                cor_mira = ROXO_CAOS

            surf_mira = pygame.Surface((30, 30), pygame.SRCALPHA)
            cx, cy = 15, 15
            pygame.draw.circle(surf_mira, cor_mira, (cx, cy), 10, 1)
            pygame.draw.line(
                surf_mira, cor_mira, (cx - 14, cy), (cx + 14, cy), 1
            )
            pygame.draw.line(
                surf_mira, cor_mira, (cx, cy - 14), (cx, cy + 14), 1
            )

            if angulo_mira != 0:
                surf_mira = pygame.transform.rotate(surf_mira, angulo_mira)

            rect_mira_surf = surf_mira.get_rect(
                center=(int(mira_x), int(mira_y))
            )
            tela_interna.blit(surf_mira, rect_mira_surf)

        if barra_amaldicoada_ativa and not animando_consumo:
            fator = barra_amaldicoada_nivel / 100.0
            cor_barra = (
                255,
                int(255 * (1.0 - fator)),
                int(255 * (1.0 - fator)),
            )

            intencidade_tremor = (
                0
                if barra_amaldicoada_nivel < 30
                else 1
                if barra_amaldicoada_nivel < 70
                else int(2 + (fator - 0.7) * 8)
            )
            shake_x = (
                random.randint(-intencidade_tremor, intencidade_tremor)
                if intencidade_tremor > 0
                else 0
            )
            shake_y = (
                random.randint(-intencidade_tremor, intencidade_tremor)
                if intencidade_tremor > 0
                else 0
            )

            pos_x, pos_y = 10 + shake_x, 10 + shake_y
            pygame.draw.rect(
                tela_interna, (50, 50, 50), (pos_x, pos_y, 100, 8)
            )
            pygame.draw.rect(
                tela_interna, cor_barra, (pos_x, pos_y, int(100 * fator), 8)
            )

            rosto = (
                '( ^_^) '
                if barra_amaldicoada_nivel < 30
                else '( ._.) '
                if barra_amaldicoada_nivel < 70
                else '( ☢_☢ )'
            )
            fonte_rosto = pygame.font.SysFont(None, 12)
            txt_rosto = fonte_rosto.render(rosto, True, cor_barra)
            tela_interna.blit(txt_rosto, (pos_x + 105, pos_y - 2))

        if mestre_ordem_ativa and not animando_consumo:
            fonte_mestre = pygame.font.SysFont(None, 15, bold=True)
            shake_mestre_x = (
                random.randint(-1, 1) if mestre_estado == 'ATIVO' else 0
            )
            shake_mestre_y = (
                random.randint(-1, 1) if mestre_estado == 'ATIVO' else 0
            )

            if mestre_estado == 'ALERTA':
                txt_mestre = fonte_mestre.render(
                    '--- O MESTRE VAI FALAR! ---', True, AMARELO
                )
                cor_borda = AMARELO
            else:
                txt_mestre = fonte_mestre.render(mestre_texto, True, VERMELHO)
                cor_borda = VERMELHO

            base_x = LARGURA // 2 - txt_mestre.get_width() // 2 + shake_mestre_x
            base_y = 4 + shake_mestre_y

            rect_fundo_txt = pygame.Rect(
                base_x - 6, base_y, txt_mestre.get_width() + 12, 16
            )
            pygame.draw.rect(tela_interna, (15, 0, 0), rect_fundo_txt)
            pygame.draw.rect(tela_interna, cor_borda, rect_fundo_txt, 1)

            tela_interna.blit(txt_mestre, (base_x, base_y + 2))

        fonte = pygame.font.SysFont(None, 16)
        texto_pontos = fonte.render(f'PONTOS: {pontos}', True, BRANCO)
        tela_interna.blit(texto_pontos, (LARGURA - 100, 8))

        if game_over:
            sombra = pygame.Surface((LARGURA, ALTURA))
            sombra.set_alpha(220)
            sombra.fill(PRETO)
            tela_interna.blit(sombra, (0, 0))

            txt_go = fonte.render('O CAOS TE ENGOLIU!', True, ROXO_CAOS)
            txt_re = fonte.render(
                "Pressione 'R' para voltar ao Menu", True, BRANCO
            )

            tela_interna.blit(
                txt_go,
                (LARGURA // 2 - txt_go.get_width() // 2, ALTURA // 2 - 15),
            )
            tela_interna.blit(
                txt_re,
                (LARGURA // 2 - txt_re.get_width() // 2, ALTURA // 2 + 5),
            )

    frame_escalado = pygame.transform.scale(
        tela_interna, (janela.get_width(), janela.get_height())
    )
    janela.blit(frame_escalado, (0, 0))

    pygame.display.flip()