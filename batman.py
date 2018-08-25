#coding:utf-8
# modulo random: necessario para gerar eventos aleatorios no jogo
# modulo os.path: necessario para direcionar a pasta que contem os arquivos de imagem
import random, os.path

# importa os modulos do pygame, necessario para criar o jogo
import pygame
from pygame.locals import *


#Variaveis do jogo
MAX_TIROS       = 4                      # Qtd maxima de balas atiradas pelo jogador
CURINGA_ODDS    = 20                     # Probabilidade de aparecer um novo inimigo
BOMBA_ODDS      = 60                     # Probabilidade de bombas cairem
CURINGA_RELOAD  = 12                     # Frames entre novos inimigos
SCREENRECT      = Rect(0, 0, 640, 480)   # Resolucao da tela
SCORE           = 0                      # Pontuacao do jogador
STR_LEVEL       = "easy"                 # Texto do level que aparecerá na tela

main_dir = os.path.split(os.path.abspath(__file__))[0]

# Função responsável para carregar uma imagem na tela
def load_image(file):
    "Carregando as imagens..."
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Erro ao carregar imagem "%s" %s'%(file, pygame.get_error()))
    return surface.convert()


# Função responsável para carregar as imagens na tela
def load_images(*files):
    imgs = []
    for file in files:
        imgs.append(load_image(file))
    return imgs


'''
Cada tipo de objeto de jogo recebe um init e uma função de atualização.
A função de atualização é chamada uma vez por quadro e é quando cada objeto
deve alterar sua posição e estado atuais. o objeto Player na verdade obtém
uma função "move" em vez de update, já que é passada informação extra
sobre o teclado.
'''

# Classe de um agente do jogo, neste caso, o jogador
class Player(pygame.sprite.Sprite):
    vel = 10
    bounce = 24
    gun_offset = -11
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1

    def move(self, direction):
        if direction: self.facing = direction
        self.rect.move_ip(direction*self.vel, 0)
        self.rect = self.rect.clamp(SCREENRECT)
        if direction < 0:
            self.image = self.images[0]
        elif direction > 0:
            self.image = self.images[1]
        self.rect.top = self.origtop - (self.rect.left//self.bounce%2)

    # retorna a posicao do agente no momento que atirou
    def gunpos(self):
        pos = self.facing*self.gun_offset + self.rect.centerx
        return pos, self.rect.top

# Classe dos agentes automatos do jogo
class Curinga(pygame.sprite.Sprite):
    vel = 13
    #taxa de mudanca das imagens entre os agentes automatos
    taxaMImg = 100        
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.facing = random.choice((-1,1)) * Curinga.vel
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing
            self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.taxaMImg%3]

# Classe da explosao (choque entre Bomba e jogador, inimigo e jogador, tiro e inimigo, bomba e terreo)
class Explosao(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0: self.kill()

# Classe de lancamento de um tiro pelo jogador
class Tiro(pygame.sprite.Sprite):
    vel = -11
    images = []
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        self.rect.move_ip(0, self.vel)
        if self.rect.top <= 0:
            self.kill()

# Classe de drop de bombas pelo inimigo
class Bomba(pygame.sprite.Sprite):
    vel = 9
    images = []
    def __init__(self, curinga):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom = curinga.rect.move(0,5).midbottom)

    def update(self):
        self.rect.move_ip(0, self.vel)
        if self.rect.bottom >= 470:
            Explosao(self)
            self.kill()

''' Dependendo da potuacao, determinadas configuracoes eh realizada 
    de forma que aumente a dificuldade do jogo '''
# Funcao responsavel pelo aumento da dificuldade
def upLevelGame():
    global MAX_TIROS, CURINGA_ODDS, BOMBA_ODDS, STR_LEVEL
    msg = "Level "+STR_LEVEL+": "+str(SCORE)+" pontos"
    pygame.display.set_caption(msg)
    if SCORE == 50:
        if MAX_TIROS > 0 and BOMBA_ODDS <= 100:
            MAX_TIROS = MAX_TIROS - 1
            CURINGA_ODDS = CURINGA_ODDS + 5
            BOMBA_ODDS = BOMBA_ODDS + 10
            STR_LEVEL = 'moderate'

    elif SCORE == 200:
        if MAX_TIROS > 0 and BOMBA_ODDS <= 100:
            MAX_TIROS = MAX_TIROS - 1
            CURINGA_ODDS = CURINGA_ODDS + 10
            BOMBA_ODDS = BOMBA_ODDS + 20
            STR_LEVEL = 'hard'
    
    elif SCORE == 400:
        if MAX_TIROS > 0 and BOMBA_ODDS <= 100:
            MAX_TIROS = 1
            CURINGA_ODDS = CURINGA_ODDS + 11
            BOMBA_ODDS = 100
            STR_LEVEL = 'insane'
    
# Funcao responsavel pelo aumento da pontuacao
def levelScore():
    global SCORE
    if SCORE < 50 :
        SCORE = SCORE + 1
    elif SCORE < 200 :
        SCORE = SCORE + 2
    else :
        SCORE = SCORE + 5

    upLevelGame()

# Funcao principal do game
def main(winstyle = 0):
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print ('Warning, no sound')
        pygame.mixer = None

    # Configurando o display
    winstyle = 0
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    #Carregando todas as possíveis imagens que o jogo utilizará
    img = load_image('player.gif')
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif')
    Explosao.images = [img, pygame.transform.flip(img, 1, 1)]
    Curinga.images = load_images('curinga1.gif', 'curinga2.gif', 'curinga3.gif')
    Bomba.images = [load_image('bomb.gif')]
    Tiro.images = [load_image('shot.gif')]

    # Janela do jogo
    icon = pygame.transform.scale(Curinga.images[0], (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Batman vs Curinga - Trabalho IA')
    pygame.mouse.set_visible(0)

    bgdtile = load_image('city.gif') # plano de fundo
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    # Carrega os Groups dos eventos do game
    curingas = pygame.sprite.Group()
    tiros = pygame.sprite.Group()
    bombas = pygame.sprite.Group()
    all = pygame.sprite.RenderUpdates()
    lastcuringa = pygame.sprite.GroupSingle()

    # Atribui grupos default para cada classe de sprite
    Player.containers = all
    Curinga.containers = curingas, all, lastcuringa
    Tiro.containers = tiros, all
    Bomba.containers = bombas, all
    Explosao.containers = all

    # Criando alguns valores iniciais
    global SCORE
    curingareload = CURINGA_RELOAD
    kills = 0
    clock = pygame.time.Clock()
    player = Player()
    Curinga()


    while player.alive(): # loop enquanto o jogador estiver vivo

        # loop para a entrada de teclado
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
        keystate = pygame.key.get_pressed()

        # Limpa os ultimos desenhos na tela
        all.clear(screen, background)

        # Atualiza todos os sprites
        all.update()

        # Movimentacao do player, pela entrada do teclado
        direction = keystate[K_RIGHT] - keystate[K_LEFT]
        # extremos da minha tela -0.5 e 0.5
        player.move(direction)
        direction += 10
        firing = keystate[K_SPACE] # Entrada do teclado para soltar um tiro
        if not player.reloading and firing and len(tiros) < MAX_TIROS:
            Tiro(player.gunpos())
        player.reloading = firing

        # Criando um novo curinga
        if curingareload:
            curingareload = curingareload - 1
        elif not int(random.randint(0,5) * CURINGA_ODDS):
            Curinga()
            curingareload = CURINGA_RELOAD
        
        # Curinga soltando bombas
        if lastcuringa and not int(random.random() * BOMBA_ODDS):
            Bomba(lastcuringa.sprite)

        # Detectando explosao
        for curinga in pygame.sprite.spritecollide(player, curingas, 1):
            Explosao(curinga)
            Explosao(player)
            levelScore()
            player.kill()

        for curinga in pygame.sprite.groupcollide(tiros, curingas, 1, 1).keys():
            Explosao(curinga)
            levelScore()

        for bomba in pygame.sprite.spritecollide(player, bombas, 1):
            Explosao(player)
            Explosao(bomba)
            player.kill()

        # Desenhando na tela todas as cenas
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        #Taxa de quadro
        clock.tick(40)

    pygame.time.wait(1000)
    pygame.quit()


# Chama a funcao main no script de execucao principal
main()
