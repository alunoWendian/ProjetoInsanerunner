import sqlite3
import pygame
import sys
import random

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
    cursor.execute('INSERT INTO placar (nome, pontos) VALUES (?, ?)', (nome, pontos))
    conn.commit()
    conn.close()

# ==========================================
# 2. CONFIGURAÇÕES DO JOGO (Pygame)
# ==========================================
pygame.init()
init_db()

LARGURA, ALTURA = 320, 180
LARGURA_TELA, ALTURA_TELA = 1280, 720

tela_interna = pygame.Surface((LARGURA, ALTURA))
janela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Insane Runner")

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

# ==========================================
# 3. LINHAS E VARIÁVEIS DE JOGO
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

chao_offset = 0
velocidade_jogo = 2.5

obstaculos = []
tempo_proximo_obstaculo = 0

# A Destruição Caótica
tropecos = 0
alcance_destruicao_atual = -15.0
pulso_caos = 0
animando_consumo = False

# Pontuação e Ajustes de Tempo
pontos = 0
acumulador_pontos = 0.0  # Para contar pontos pela metade da velocidade
INTERVALO_MODIFICADOR = 1000
proximo_gatilho_pontos = INTERVALO_MODIFICADOR

game_over = False

# ESTADOS DO JOGO: 'CORRIDA' ou 'SELECAO'
estado_jogo = 'CORRIDA'

# Sistema da Grade de Seleção
grade_x = LARGURA + 20
opcoes_grade = ["DISPARADOR", "DISPARADOR", "DISPARADOR"]

# Entidade: Disparador
disparador_ativo = False
mira_x, mira_y = 0, 0
temporizador_disparo = 0
estado_disparo = 'DESATIVADO'  # 'SEGUINDO', 'TRAVADO_PISCANDO', 'ATIRANDO'
tempo_piscada = 0

# ==========================================
# 4. LOOP PRINCIPAL
# ==========================================
while True:
    relogio.tick(60)
    teclas = pygame.key.get_pressed()
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if evento.type == pygame.KEYDOWN:
            if not game_over:
                # Troca de linha
                if (evento.key == pygame.K_UP or evento.key == pygame.K_w) and linha_atual > 0:
                    linha_atual -= 1
                if (evento.key == pygame.K_DOWN or evento.key == pygame.K_s) and linha_atual < 2 and not deslizando:
                    linha_atual += 1
                    
                # Pulo
                if evento.key == pygame.K_SPACE and not pulo and not deslizando:
                    pulo = True
                    vel_pulo = -5.5
            else:
                if evento.key == pygame.K_r:
                    game_over = False
                    animando_consumo = False
                    tropecos = 0
                    alcance_destruicao_atual = -15.0
                    pontos = 0
                    acumulador_pontos = 0.0
                    proximo_gatilho_pontos = INTERVALO_MODIFICADOR
                    player_offset_x = 100
                    linha_atual = 1
                    obstaculos.clear()
                    tempo_proximo_obstaculo = 0
                    disparador_ativo = False
                    estado_disparo = 'DESATIVADO'
                    estado_jogo = 'CORRIDA'

    if not game_over:
        chao_offset = (chao_offset + velocidade_jogo) % 20

        # Posição e Hitbox do Jogador
        y_base_player = LINHAS_Y[linha_atual]
        h_player = player_altura_deslize if deslizando else player_altura_normal
        y_player = y_base_player - h_player + int(altura_pulo)
        rect_player = pygame.Rect(player_offset_x, y_player, player_largura, h_player)

        # Deslize e Movimentação Horizontal
        if (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT] or teclas[pygame.K_c]) and not pulo:
            deslizando = True
        else:
            deslizando = False

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            player_offset_x -= 1.8
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            player_offset_x += 1.8

        player_offset_x = max(20, min(LARGURA - 30, player_offset_x))

        # Física do Pulo
        if pulo:
            altura_pulo += vel_pulo
            vel_pulo += gravidade
            if altura_pulo >= 0:
                altura_pulo = 0
                pulo = False

        # ----------------------------------------------------
        # LÓGICA DO ESTADO DE CORRIDA
        # ----------------------------------------------------
        if estado_jogo == 'CORRIDA':
            # Ganho de pontos reduzido pela metade (+0.5 por frame em vez de +1)
            acumulador_pontos += 0.5
            pontos = int(acumulador_pontos)

            # Checa se atingiu o gatilho dos 1000 pontos
            if pontos >= proximo_gatilho_pontos:
                estado_jogo = 'SELECAO'
                grade_x = LARGURA + 20
                proximo_gatilho_pontos += INTERVALO_MODIFICADOR

            # Geração de Obstáculos
            tempo_proximo_obstaculo -= 1
            if tempo_proximo_obstaculo <= 0 and not animando_consumo:
                tipo = random.choice(['pedra_normal', 'pedra_grande', 'pedra_deslize'])
                linha_sorteada = random.randint(0, 2)
                
                if tipo == 'pedra_normal':
                    obstaculos.append({'tipo': 'pedra_normal', 'x': LARGURA + 10, 'linha': linha_sorteada, 'largura': 12, 'altura': 10, 'offset_y': 0})
                elif tipo == 'pedra_grande':
                    obstaculos.append({'tipo': 'pedra_grande', 'x': LARGURA + 10, 'linha': linha_sorteada, 'largura': 16, 'altura': 50, 'offset_y': 0})
                elif tipo == 'pedra_deslize':
                    obstaculos.append({'tipo': 'pedra_deslize', 'x': LARGURA + 10, 'linha': linha_sorteada, 'largura': 14, 'altura': 40, 'offset_y': 11})
                
                tempo_proximo_obstaculo = random.randint(70, 130)

        # ----------------------------------------------------
        # LÓGICA DO ESTADO DE SELEÇÃO (GRADE AVANÇANDO)
        # ----------------------------------------------------
        elif estado_jogo == 'SELECAO':
            grade_x -= 1.2  # Grade avança em direção ao jogador

            # Colisão com a Grade (na linha do jogador ou se a grade ultrapassá-lo)
            if grade_x <= player_offset_x + player_largura:
                disparador_ativo = True
                temporizador_disparo = 180
                estado_jogo = 'CORRIDA'

        # Movimentação e Colisão das Pedras
        for obs in obstaculos[:]:
            obs['x'] -= velocidade_jogo
            
            if obs['linha'] == linha_atual and not animando_consumo:
                y_obs = LINHAS_Y[obs['linha']] - obs['altura'] - obs['offset_y']
                rect_obs = pygame.Rect(obs['x'], y_obs, obs['largura'], obs['altura'])

                if rect_player.colliderect(rect_obs):
                    tropecos += 1
                    obstaculos.remove(obs)
                    if tropecos >= 3:
                        animando_consumo = True
                    continue

            if obs['x'] < -20:
                obstaculos.remove(obs)

        # ----------------------------------------------------
        # COMPORTAMENTO DO DISPARADOR (ENTIDADE)
        # ----------------------------------------------------
        if disparador_ativo and not animando_consumo:
            temporizador_disparo -= 1

            if estado_disparo == 'DESATIVADO':
                if temporizador_disparo <= 0:
                    estado_disparo = 'SEGUINDO'
                    temporizador_disparo = 120

            elif estado_disparo == 'SEGUINDO':
                mira_x += (rect_player.centerx - mira_x) * 0.1
                mira_y += (rect_player.centery - mira_y) * 0.1
                
                if temporizador_disparo <= 0:
                    estado_disparo = 'TRAVADO_PISCANDO'
                    temporizador_disparo = 45
                    tempo_piscada = 0

            elif estado_disparo == 'TRAVADO_PISCANDO':
                tempo_piscada += 1
                if temporizador_disparo <= 0:
                    estado_disparo = 'ATIRANDO'

            elif estado_disparo == 'ATIRANDO':
                rect_mira = pygame.Rect(mira_x - 6, mira_y - 6, 12, 12)
                if rect_player.colliderect(rect_mira):
                    tropecos += 1
                    if tropecos >= 3:
                        animando_consumo = True

                estado_disparo = 'DESATIVADO'
                temporizador_disparo = random.randint(200, 350)

        # Avanço do Caos
        if not animando_consumo:
            alvo_destruicao = -15 + (tropecos * 35)
            alcance_destruicao_atual += (alvo_destruicao - alcance_destruicao_atual) * 0.08
        else:
            alcance_destruicao_atual += 5
            if alcance_destruicao_atual >= LARGURA:
                game_over = True
                salvar_pontuacao("Visitante Feira", pontos)

        pulso_caos = (pulso_caos + 0.12) % 8

    # ==========================================
    # 5. RENDERIZAÇÃO
    # ==========================================
    tela_interna.fill(PRETO)

    # 1. Pistas
    for y in LINHAS_Y:
        pygame.draw.line(tela_interna, (30, 30, 40), (0, y), (LARGURA, y), 1)
        for x in range(-20 + int(-chao_offset), LARGURA + 20, 20):
            pygame.draw.line(tela_interna, (50, 50, 65), (x, y), (x + 8, y), 1)

    # 2. Desenho do Disparador no Cenário (Fundo)
    if disparador_ativo:
        pygame.draw.rect(tela_interna, (80, 20, 30), (LARGURA - 25, 25, 12, 18))
        pygame.draw.circle(tela_interna, VERMELHO, (LARGURA - 19, 30), 3)

    # 3. Obstáculos
    for obs in obstaculos:
        if obs['tipo'] == 'pedra_deslize':
            y_visivel = LINHAS_Y[obs['linha']] - 18 - obs['offset_y']
            pygame.draw.rect(tela_interna, CINZA_PEDRA_DESLIZE, (obs['x'], y_visivel, obs['largura'], 18))
        else:
            y_obs = LINHAS_Y[obs['linha']] - obs['altura'] - obs['offset_y']
            cor = CINZA_PEDRA_GRANDE if obs['tipo'] == 'pedra_grande' else CINZA_PEDRA
            pygame.draw.rect(tela_interna, cor, (obs['x'], y_obs, obs['largura'], obs['altura']))

    # 4. Grade de Seleção de Modificadores
    if estado_jogo == 'SELECAO':
        pygame.draw.rect(tela_interna, VERDE_GRADE, (grade_x, 30, 6, 130), 2)
        fonte_m = pygame.font.SysFont(None, 12)
        
        for i, y_linha in enumerate(LINHAS_Y):
            pygame.draw.line(tela_interna, VERDE_GRADE, (grade_x, y_linha - 20), (grade_x + 60, y_linha - 20), 1)
            txt_mod = fonte_m.render(opcoes_grade[i], True, BRANCO)
            tela_interna.blit(txt_mod, (grade_x + 8, y_linha - 15))

    # 5. Jogador
    pygame.draw.rect(tela_interna, CINZA_JOGADOR, rect_player)

    # 6. Mira do Disparador
    if estado_disparo in ['SEGUINDO', 'TRAVADO_PISCANDO', 'ATIRANDO']:
        cor_mira = VERMELHO
        if estado_disparo == 'TRAVADO_PISCANDO':
            cor_mira = AMARELO if (tempo_piscada // 4) % 2 == 0 else VERMELHO
        elif estado_disparo == 'ATIRANDO':
            cor_mira = BRANCO

        pygame.draw.circle(tela_interna, cor_mira, (int(mira_x), int(mira_y)), 7, 1)
        pygame.draw.line(tela_interna, cor_mira, (int(mira_x) - 10, int(mira_y)), (int(mira_x) + 10, int(mira_y)), 1)
        pygame.draw.line(tela_interna, cor_mira, (int(mira_x), int(mira_y) - 10), (int(mira_x), int(mira_y) + 10), 1)

    # 7. A Destruição Caótica
    largura_visivel = int(alcance_destruicao_atual + pulso_caos)
    if largura_visivel > 0:
        pygame.draw.rect(tela_interna, DESTRUICAO_PRETO, (0, 0, largura_visivel, ALTURA))
        pygame.draw.line(tela_interna, ROXO_CAOS, (largura_visivel, 0), (largura_visivel, ALTURA), 2)
        for i in range(0, ALTURA, 12):
            offset_fogo = (int(pulso_caos) + i) % 7
            pygame.draw.rect(tela_interna, ROXO_ESCURO, (largura_visivel - 6 + offset_fogo, i, 4, 6))

    # 8. HUD (Pontuação)
    fonte = pygame.font.SysFont(None, 16)
    texto_pontos = fonte.render(f"PONTOS: {pontos}", True, BRANCO)
    tela_interna.blit(texto_pontos, (LARGURA - 100, 8))

    # 9. Game Over
    if game_over:
        sombra = pygame.Surface((LARGURA, ALTURA))
        sombra.set_alpha(220)
        sombra.fill(PRETO)
        tela_interna.blit(sombra, (0, 0))
        
        txt_go = fonte.render("O CAOS TE ENGOLIU!", True, ROXO_CAOS)
        txt_re = fonte.render("Pressione 'R' para reiniciar", True, BRANCO)
        
        tela_interna.blit(txt_go, (LARGURA // 2 - txt_go.get_width() // 2, ALTURA // 2 - 15))
        tela_interna.blit(txt_re, (LARGURA // 2 - txt_re.get_width() // 2, ALTURA // 2 + 5))

    frame_escalado = pygame.transform.scale(tela_interna, (LARGURA_TELA, ALTURA_TELA))
    janela.blit(frame_escalado, (0, 0))

    pygame.display.flip()