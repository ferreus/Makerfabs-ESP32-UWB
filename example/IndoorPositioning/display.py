import pygame
import sys
import threading
import queue
import socket
import json

q = queue.Queue()

running = True


def worker():
    TCP_IP = "0.0.0.0"
    TCP_PORT = 4545
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen()

    while(running):
        s, addr = sock.accept()
        while(running):
            msg = s.recv(1024).decode('UTF-8')
            print(msg)

            uwb_list = []

            try:
                uwb_data = json.loads(msg)
                print(uwb_data)

                uwb_list = uwb_data["links"]
                q.put(uwb_data)
                print("********************\nlinks:\n")
                for uwb_archor in uwb_list:
                    print(uwb_archor)

            except Exception as e:
                print(e)
                print(msg)
            print("")


# Initialise pygame
pygame.init()

threading.Thread(target=worker, daemon=True).start()

# Create the screen

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.set_alpha(None)

# Change the title and the icon

pygame.display.set_caption('MARINKA')
#icon = pygame.image.load('IA.png')
# pygame.display.set_icon(icon)

# Anchors


class Anchor:
    def __init__(self, addr, pos):
        self.img = pygame.image.load('esp32.png')
        self.img = pygame.transform.scale(
            self.img, (self.img.get_width()//2, self.img.get_height() // 2))
        self.w = self.img.get_width()
        self.h = self.img.get_height()
        self.cx, self.cy = pos
        font = pygame.font.SysFont(None, 24)
        self.label = font.render(str(addr), True, (255, 255, 255))

    def draw(self):
        screen.blit(self.img, (self.cx-self.w/2, self.cy-self.h/2))
        screen.blit(self.label, (self.cx - self.label.get_width() /
                                 2-20, self.cy - self.label.get_height() / 2))

    def hit_test(self, pos):
        x, y = pos
        if x >= self.cx - self.w/2 and x <= self.cx + self.w/2 and y >= self.cy - self.h/2 and y <= self.cy + self.h/2:
            return True

        return False


class Room:
    def __init__(self, w, h):
        self.player = pygame.image.load('player.png')
        self.player = pygame.transform.scale(
            self.player, (self.player.get_width()//2, self.player.get_height() // 2))
        self.heading = 0
        self.heading_offset = 0
        self.sw = SCREEN_WIDTH
        self.sh = SCREEN_HEIGHT
        self.p2m = min((self.sw - 100) / w, (self.sh - 100) / h)
        self.links = None

        self.w = w*self.p2m
        self.h = h*self.p2m
        print("p2m:", self.p2m, self.w, self.h)

        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 255)
        self.yellow = (0, 255, 255)

        l = int(self.sw/2 - self.w/2)
        t = int(self.sh/2 - self.h/2)
        anchors = []
        anchors.append(Anchor(0x1, (l, t)))
        anchors.append(Anchor(0x2, (l+self.w, t)))
        anchors.append(Anchor(0x3, (l, t+self.h)))
        anchors.append(Anchor(0x4, (l+self.w, t+self.h)))
        self.anchors = anchors

    def get_left(self):
        return self.sw/2 - self.w/2

    def get_top(self):
        return self.sh/2 - self.h/2


    def set_heading_offset(self):
        self.heading_offset = self.heading

    def draw(self):
        l = int(self.sw/2 - self.w/2)
        t = int(self.sh/2 - self.h/2)
        size = 5
        pygame.draw.rect(screen, (255, 255, 255), (l, t, self.w, size))
        pygame.draw.rect(screen, (255, 255, 255), (l, t, size, self.h))
        pygame.draw.rect(screen, (255, 255, 255),
                         (l, t+self.h-size, self.w, size))
        pygame.draw.rect(screen, (255, 255, 255),
                         (l+self.w-size, t, size, self.h))
        for a in self.anchors:
            a.draw()
        self.draw_links()

    def draw_links(self):
        if self.links is None:
            return

        colors = [self.red, self.green, self.blue, self.yellow]
        points = []
        for l in self.links:
            name = int(l["A"])-1
            a = self.anchors[name]
            c = colors[name]
            r = int(abs(float(l["R"])*self.p2m))
            points.append((int(a.cx), int(a.cy), int(abs(r))))
            pygame.draw.circle(screen, c, (int(a.cx), int(a.cy)), r, 2)

        if len(points) == 3:
            #p1 = self.track_anchor(points[0], points[1], points[2])
            #p2 = self.track_anchor(points[0], points[1], points[3])
            #p3 = self.track_anchor(points[1], points[2], points[3])
            p1 = points[0]
            p2 = points[1]
            p3 = points[2]
            pf = self.track_anchor(p1, p2, p3)
            pygame.draw.circle(screen, colors[0], (p1[0], p1[1]), 5, 2)
            pygame.draw.circle(screen, colors[1], (p2[0], p2[1]), 5, 2)
            pygame.draw.circle(screen, colors[2], (p3[0], p3[1]), 5, 2)
            #pygame.draw.circle(screen, colors[3], (pf[0], pf[1]), 5, 2)
            #img = pygame.transform.rotate(self.player,self.heading)
            img = self.rot_center(self.player,self.heading-self.heading_offset)
            screen.blit(img, (pf[0]-self.player.get_width()//2,pf[1] - self.player.get_height()//2))

    def rot_center(self, img, angle):
        loc = img.get_rect().center
        ret = pygame.transform.rotate(img, angle)
        ret.get_rect().center = loc
        return ret

    def track_anchor(self, a, b, c):
        x1, y1, r1 = a
        x2, y2, r2 = b
        x3, y3, r3 = c
        A = 2*x2 - 2*x1
        B = 2*y2 - 2*y1
        C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2*x3 - 2*x2
        E = 2*y3 - 2*y2
        F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2
        x = (C*E - F*B) / ((E*A - B*D)+0.1)
        y = (C*D - A*F) / ((B*D - A*E)+0.1)
        return (int(x), int(y), 1)

    def set_links(self, data):
        if len(data["links"])>=3:
            self.links = data["links"]
        self.heading = data["heading"]


rw = 10
rh = 8
if len(sys.argv) == 3:
    rw = int(sys.argv[1])
    rh = int(sys.argv[2])
room = Room(rw, rh)


def text_objects(text, font):
    textSurface = font.render(text, True, (100, 100, 100))
    return textSurface, textSurface.get_rect()


# Running the window
i = 0
running = True
draging = None
while running:
    mx, my = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                room.set_heading_offset()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            for a in room.anchors:
                if a.hit_test((mx, my)):
                    draging = a
                    break

        elif event.type == pygame.MOUSEBUTTONUP:
            draging = None

        elif event.type == pygame.MOUSEMOTION:
            if draging is not None:
                draging.cx = mx
                draging.cy = my

    # clear the display
    screen.fill((30, 30, 30))

    room.draw()

    try:
        item = q.get_nowait()
        print("Main loop, got item:", item)
        room.set_links(item)
        q.task_done()
    except:
        pass

    # update the dispalay
    pygame.display.flip()
