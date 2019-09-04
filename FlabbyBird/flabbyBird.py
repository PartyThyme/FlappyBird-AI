import pygame
import neat
import time
import os
import random
pygame.font.init()

# Note initialised variables with capital to present that they are constant

WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

# Change the scale of the image to be double size and load images from the file "Imgs"
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25           # Maximum rotation of the bird
    ROTATION_VELOCITY = 20      # Speed of angle change
    ANIMATION_TIME = 5          # How long for each animation

    def __init__(self, x, y):
        self.x = x
        self.y = y
        # For initial position
        self.tilt = 0           # Initialise the position of the bird
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5       # Move up
        self.tick_count = 0
        self.height = self.y   # Previous state of the bird after it jumped

    def move(self):
        self.tick_count += 1    # How many second it been moving
        # How many pixel move up and down
        # Equation Distance = v*t +1.5*t^2
        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        # Prevent velocity from moving far up or far down
        if d >= 16:
            d = d/abs(d)*16     # or 16

        # Control jump height
        if d < 0:
            d -= 2

        #  Calculate current height
        self.y = self.y + d

        # Bird going upward and control the angle of image to be 25 (MAX_ROTATION)
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        # Bird going downward and control the angle of image to 50 to make it look directly dive down
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    def draw(self, win):
        self.img_count += 1

        # "ANIMETION_TIME = 5"
        # For wings flapping up and down
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0          # Reset image count

        # Check if the bird is diving downward
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        # transform for the top pipe because the origina image is only for bottom pipe
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()       # Random define

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, win):
        """Pixel perfect collision - because the picture image is in pixel and the program
        will detects the corner edge of the image (The user will not be able to see)
        The use of this function is to check if the wanted pixels of 2 images are touching each other"""

        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # For bird and top mask
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # If not collide will return none
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        if top_point or bottom_point:
            # The game ends
            return True

        # Keep going
        return False

# Make sure the base image will reset after the program reached the end
class Base:
    """The idea of this class is to 2 base image to queue each other on
    the display and after display and keep them circle around till the game end"""
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # Check if any of them is off the screen (left hand side) then put them at the back of the queue
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))




def draw_window(win, birds, pipes, base, score, gen):
    # blit - draw
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    # bird = Bird(230,350)
    global GEN
    GEN += 1
    nets = []
    genome = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g,config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        genome.append(g)

    base = Base(730)
    pipes = [Pipe(700)]
    score = 0
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    # How fast the program run doesn't depend on computer
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            genome[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()


        # bird.move()
        add_pipe = False
        remove = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird, win):
                    genome[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    genome.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in genome:
                g.fitness += 5
            pipes.append(Pipe(500))

        for pipe in remove:
            pipes.remove(pipe)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                genome.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)

    # pygame.quit()
    # quit()

# main()


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main ,50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir,"config-feedforward.txt")
    run(config_path)
