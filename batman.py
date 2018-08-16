#!/usr/bin/env python
#coding:utf-8

import random, os.path

#importa os modulos do pygame
import pygame
from pygame.locals import *

#Analisa a possibilidade de carregar imagens em BMP
if not pygame.image.get_extended():
    raise SystemExit("O modulo da imagem estentida eh obrigatorio")


#Constantes do jogo
MAX_SHOTS      = 3                      # Qtd máxima de balas atiradas pelo jogador
CURINGA_ODDS     = 22                     # Probabilidade de aparecer um novo inimigo
BOMB_ODDS      = 60                     # Probabilidade de bombas cairem
CURINGA_RELOAD   = 12                     # frames entre novos inimigos
SCREENRECT     = Rect(0, 0, 640, 480)   # resolucao da tela
SCORE          = 0                      # pontuacao do jogador

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


class somGame:
    def play(self): pass

def load_sound(file):
    if not pygame.mixer: return somGame()
    file = os.path.join(main_dir, 'data', file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print ('Incapaz de carregar, %s' % file)
    return somGame()



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
        # print 'self.facing = '+str(self.facing)
        # print 'self.gun_offset = '+str(self.gun_offset)
        # print 'self.rect.centerx = '+str(self.rect.centerx)
        pos = self.facing*self.gun_offset + self.rect.centerx
        return pos, self.rect.top


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


class Explosion(pygame.sprite.Sprite):
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


class Shot(pygame.sprite.Sprite):
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


class Bomb(pygame.sprite.Sprite):
    vel = 9
    images = []
    def __init__(self, curinga):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=
                    curinga.rect.move(0,5).midbottom)

    def update(self):
        self.rect.move_ip(0, self.vel)
        if self.rect.bottom >= 470:
            Explosion(self)
            self.kill()


class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "Pontos: %d" % SCORE
            self.image = self.font.render(msg, 0, self.color)



def main(winstyle = 0):
    # Initialize pygame
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print ('Warning, no sound')
        pygame.mixer = None

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    #Load images, assign to sprite classes
    #(do this before the classes are used, after screen setup)
    img = load_image('player.gif')
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif')
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]
    Curinga.images = load_images('curinga1.gif', 'curinga2.gif', 'curinga3.gif')
    Bomb.images = [load_image('bomb.gif')]
    Shot.images = [load_image('shot.gif')]

    #decorate the game window
    icon = pygame.transform.scale(Curinga.images[0], (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Batman vs Curinga')
    pygame.mouse.set_visible(0)

    #create the background, tile the bgd image
    bgdtile = load_image('city.gif')
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    #load the sound effects
    boom_sound = load_sound('boom.wav')
    shoot_sound = load_sound('car_door.wav')
    if pygame.mixer:
        music = os.path.join(main_dir, 'data', 'house_lo.wav')
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

    # Initialize Game Groups
    curingas = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    all = pygame.sprite.RenderUpdates()
    lastcuringa = pygame.sprite.GroupSingle()

    #assign default groups to each sprite class
    Player.containers = all
    Curinga.containers = curingas, all, lastcuringa
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Score.containers = all

    #Create Some Starting Values
    global score
    curingareload = CURINGA_RELOAD
    kills = 0
    clock = pygame.time.Clock()

    #initialize our starting sprites
    global SCORE
    player = Player()
    Curinga() #note, this 'lives' because it goes into a sprite group
    if pygame.font:
        all.add(Score())


    while player.alive():

        #get input
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
        keystate = pygame.key.get_pressed()

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        #update all the sprites
        all.update()

        #handle player input
        direction = keystate[K_RIGHT] - keystate[K_LEFT]
        # print 'direction = '+str(direction)
        # extremos da minha tela -0.5 e 0.5
        player.move(direction)
        direction += 10
        firing = keystate[K_SPACE]
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gunpos())
            shoot_sound.play()
        player.reloading = firing

        # Criando um novo curinga
        if curingareload:
            curingareload = curingareload - 1
        elif not int(random.random() * CURINGA_ODDS):
            Curinga()
            curingareload = CURINGA_RELOAD

        # Drop bombs
        if lastcuringa and not int(random.random() * BOMB_ODDS):
            Bomb(lastcuringa.sprite)

        # Detect collisions
        for curinga in pygame.sprite.spritecollide(player, curingas, 1):
            boom_sound.play()
            Explosion(curinga)
            Explosion(player)
            SCORE = SCORE + 1
            player.kill()

        for curinga in pygame.sprite.groupcollide(shots, curingas, 1, 1).keys():
            boom_sound.play()
            Explosion(curinga)
            SCORE = SCORE + 1

        for bomb in pygame.sprite.spritecollide(player, bombs, 1):
            boom_sound.play()
            Explosion(player)
            Explosion(bomb)
            player.kill()

        #draw the scene
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        #cap the framerate
        clock.tick(40)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.time.wait(1000)
    pygame.quit()



#call the "main" function if running this script
if __name__ == '__main__': main()
