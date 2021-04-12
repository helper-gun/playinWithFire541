import turtle
import random
import time
import math
import gym
from gym.utils import seeding

#BIL 541 Hasan Alper Güneş - Emre Özçelik
#Referans: Hennie de Harder
#refence source work thanks to https://github.com/henniedeharder/snake

UNIT_LENGTH = 20
HEIGHT = UNIT_LENGTH    # number of steps vertically from wall to wall of screen
WIDTH = UNIT_LENGTH    # number of steps horizontally from wall to wall of screen
PIXEL_H = 20*HEIGHT  # pixel height + border on both sides
PIXEL_W = 20*WIDTH   # pixel width + border on both sides

SLEEP = 0.1     # time to wait between steps

BOX_NUMBER = 100
GAME_TITLE = 'PlayingWithFire'
BG_COLOR = 'gray'

BOMBER_SHAPE = 'square'
BOMBER_COLOR = 'black'
BOMBER_START_LOC_H = 0
BOMBER_START_LOC_V = 0

BOX_SHAPE = 'square'
BOX_COLOR = 'green'

BOMB_SHAPE = 'circle'
BOMB_COLOR = 'red'

debug_is_on = False

class Bomber(gym.Env):

    def __init__(self, human=False, env_info={'state_space':None}):
        super(Bomber, self).__init__()

        self.done = False
        self.seed()
        self.reward = 0
        self.action_space = 5
        self.state_space = 16

        self.total, self.maximum = 0, 0
        self.human = human
        self.env_info = env_info

        ## GAME CREATION WITH TURTLE KUTUPHANESI
        # screen/background
        self.win = turtle.Screen()
        self.win.title(GAME_TITLE)
        self.win.bgcolor(BG_COLOR)
        self.win.tracer(0)
        self.win.setup(width=PIXEL_W+32, height=PIXEL_H+32)
                
        # bomber
        self.bomber = turtle.Turtle()
        self.bomber.shape(BOMBER_SHAPE)
        self.bomber.speed(0)
        self.bomber.penup()
        self.bomber.color(BOMBER_COLOR)
        self.bomber.goto(BOMBER_START_LOC_H, BOMBER_START_LOC_V)
        self.bomber.direction = 'stop'
               
        # bomb
        self.bomb = turtle.Turtle()
        self.bomb.speed(0)
        self.bomb.shape(BOMB_SHAPE)
        self.bomb.color(BOMB_COLOR)
        self.bomb.penup()
        self.bomb.goto(1000,1000) #ekranda gösterilmeyen koordinatlar
        self.bomb_location_x = 1000
        self.bomb_location_y = 1000
        self.bomb_timer = 3
        self.bomb_planted = False
        self.plant_warning = False
        
        # boxes
        self.box_X = []
        self.box_Y = []
        for i in range(BOX_NUMBER):
            #self.box_X.append(self.random_coor())
            self.box_X.append(20*(-9 + 2*(i%10)))
            #self.box_Y.append(self.random_coor())
            if i < 10:
                self.box_Y.append(20*(-9))
            elif i < 20:
                self.box_Y.append(20*(-7))
            elif i < 30:
                self.box_Y.append(20*(-5))
            elif i < 40:
                self.box_Y.append(20*(-3))
            elif i < 50:
                self.box_Y.append(20*(-1))
            elif i < 60:
                self.box_Y.append(20*(1))
            elif i < 70:
                self.box_Y.append(20*(3))
            elif i < 80:
                self.box_Y.append(20*(5))
            elif i < 90:
                self.box_Y.append(20*(7))
            else:
                self.box_Y.append(20*(9))
        self.box_Exist = []
        for i in range(BOX_NUMBER):
            self.box_Exist.append(True)
        
        # box turtle
        self.box = []
        for i in range(len(self.box_Exist)):
            self.box.append(turtle.Turtle())
            self.box[i].speed(0)
            self.box[i].shape(BOX_SHAPE)
            self.box[i].color(BOX_COLOR)
            self.box[i].penup()
            #self.box[i].hideturtle()
            self.box[i].goto(self.box_X[i],self.box_Y[i])
            #self.box[i].write(f'{i}', align='center', font=('Courier', 14, 'normal'))

        # distance between box and bomber
        self.massCenterX, self.massCenterY = self.mass_center()
        self.dist2 = math.sqrt((self.bomber.xcor()-self.massCenterX)**2 + (self.bomber.ycor()-self.massCenterY)**2)
        
        # score
        self.score = turtle.Turtle()
        self.score.speed(0)
        self.score.color('black')
        self.score.penup()
        self.score.hideturtle()
        self.score.goto(0, 100)
        self.score.write(f"Total: {self.total}   Highest: {self.maximum}", align='center', font=('Courier', 18, 'normal'))
        self.prev_score = 0

        # control
        self.win.listen()
        self.win.onkey(self.go_up, 'Up')
        self.win.onkey(self.go_right, 'Right')
        self.win.onkey(self.go_down, 'Down')
        self.win.onkey(self.go_left, 'Left')
        self.win.onkey(self.plant_bomb, 'space')
        self.keyPressed = False
        self.feasible = True
        self.bomb_got_empty = False
        self.collision = False
        self.heart_beat_deposit = 800
        self.temporary = 0
        
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
    
    def random_coor(self):
        coor = 20*random.randint(-WIDTH/2, WIDTH/2)
        return coor   
     
    def boxCollisionCheck(self, boxHead): #hareket yönünde çarpışma
        boxDistance = 1000
        if self.bomber.direction == 'up':
            boxDistance = math.sqrt((self.bomber.xcor()-boxHead.xcor())**2 + (self.bomber.ycor()+20-boxHead.ycor())**2)
        if self.bomber.direction == 'down':
            boxDistance = math.sqrt((self.bomber.xcor()-boxHead.xcor())**2 + (self.bomber.ycor()-20-boxHead.ycor())**2)
        if self.bomber.direction == 'right':
            boxDistance = math.sqrt((self.bomber.xcor()+20-boxHead.xcor())**2 + (self.bomber.ycor()-boxHead.ycor())**2)
        if self.bomber.direction == 'left':
            boxDistance = math.sqrt((self.bomber.xcor()-20-boxHead.xcor())**2 + (self.bomber.ycor()-boxHead.ycor())**2)
        return boxDistance  
    
    def bombCollisonCheck(self): #bomba patladığında etkisi
        bombDistance = 1000
        if self.bomber.direction == 'up':
            bombDistance = math.sqrt((self.bomber.xcor()-self.bomb_location_x)**2 + (self.bomber.ycor()+20-self.bomb_location_y)**2)
        if self.bomber.direction == 'down':
            bombDistance = math.sqrt((self.bomber.xcor()-self.bomb_location_x)**2 + (self.bomber.ycor()-20-self.bomb_location_y)**2)
        if self.bomber.direction == 'right':
            bombDistance = math.sqrt((self.bomber.xcor()+20-self.bomb_location_x)**2 + (self.bomber.ycor()-self.bomb_location_y)**2)
        if self.bomber.direction == 'left':
            bombDistance = math.sqrt((self.bomber.xcor()-20-self.bomb_location_x)**2 + (self.bomber.ycor()-self.bomb_location_y)**2)
        return bombDistance

    def move_bomber(self):
        minimumDistance = 99999
        for i in range(len(self.box)):
            if self.box_Exist[i]:
                temp = self.boxCollisionCheck(self.box[i])
                if temp < minimumDistance:
                    minimumDistance = temp;
        #print(f'md = {minimumDistance}')
        if minimumDistance > self.bombCollisonCheck():
            minimumDistance = self.bombCollisonCheck()
        #print(f'mdnew = {minimumDistance}')   
        if minimumDistance > 0:
            if self.bomber.direction == 'up':
                y = self.bomber.ycor()
                self.bomber.sety(y + 20)
            if self.bomber.direction == 'right':
                x = self.bomber.xcor()
                self.bomber.setx(x + 20)
            if self.bomber.direction == 'down':
                y = self.bomber.ycor()
                self.bomber.sety(y - 20)
            if self.bomber.direction == 'left':
                x = self.bomber.xcor()
                self.bomber.setx(x - 20)
            if self.bomber.direction == 'space':
                if self.bomb_planted == False:
                    bomb_x = self.bomber.xcor()
                    bomb_y = self.bomber.ycor()
                    self.bomb.setx(bomb_x)
                    self.bomb.sety(bomb_y)
                    self.bomb_location_x = bomb_x
                    self.bomb_location_y = bomb_y
                    self.bomb_planted = True
                    self.plant_warning = True
                    self.bomb_timer = 3 
                else:
                    self.bomb_timer +=1 #bunu silince sayiyor
            if self.bomb_planted == True :
                self.bomb_timer -=1 
        else:
            self.collision = True
            
    #aracıya tanımlı hareketler aynı zamanda oyuncuya da tanımlı
    def go_up(self):
        self.bomber.direction = "up"
        self.keyPressed = True
    
    
    def go_down(self):
        self.bomber.direction = "down"
        self.keyPressed = True
    
    
    def go_right(self):
        self.bomber.direction = "right"
        self.keyPressed = True
    
    
    def go_left(self):
        self.bomber.direction = "left"
        self.keyPressed = True


    def plant_bomb(self):
        self.bomber.direction = "space"
        self.keyPressed = True
    
    def explode(self): #patlama fonksiyonu
        temp_bomb_timer = self.bomb_timer
        self.prev_score = self.total
        for i in range(len(self.box)):
            if self.box_Exist[i] and self.bomb_timer == 0:
                if self.box_explotionCheck(self.box[i]) < 25:
                    #print("box hit")
                    self.box[i].goto(1000,1000)
                    self.box_Exist[i] = False
                    self.update_score()
                    self.bomb_got_empty = False 
        if self.prev_score == self.total:
            self.bomb_got_empty = True
                
        if temp_bomb_timer == 0:
            self.bomb.goto(1000,1000)
            self.bomb_planted = False
            self.bomb_timer = 3
            self.bomb_location_x = 1000
            self.bomb_location_y = 1000
            return True
        else:
            return False
                
    def box_explotionCheck(self, boxHead):
        meter = math.sqrt((self.bomb_location_x-boxHead.xcor())**2 + (self.bomb_location_y-boxHead.ycor())**2)    
        return meter
    
    def update_score(self):
        self.total += 1
        if self.total >= self.maximum: 
            self.maximum = self.total
        self.score.clear()
        self.score.write(f"Total: {self.total}   Highest: {self.maximum}", align='center', font=('Courier', 18, 'normal'))


    def reset_score(self):
        print("restart")
        self.score.clear()
        self.total = 0
        self.bomb_timer = 3
        self.score.write(f"Total: {self.total}   Highest: {self.maximum}", align='center', font=('Courier', 18, 'normal'))
                    
    
    def measure_distance(self):
        self.prev_dist2 = self.dist2
        self.massCenterX, self.massCenterY = self.mass_center()
        self.dist2 = math.sqrt((self.bomber.xcor()-self.massCenterX)**2 + (self.bomber.ycor()-self.massCenterY)**2)

        #durum uzayı için tanımlanan ağırlık ortalama fonksiyonu
    def mass_center(self):
        box_mass_sum_x = 0
        box_mass_sum_y = 0
        box_alive = 0
        for i in range(len(self.box)):
            if self.box_Exist[i]:
                box_alive += 1
                box_mass_sum_x += self.box[i].xcor()
                box_mass_sum_y += self.box[i].ycor()
        
        if box_alive > 0:
            boxMx, boxMy =  int(box_mass_sum_x/box_alive), int(box_mass_sum_y/box_alive)
        else:
            boxMx, boxMy = 0, 0
        #boxMx, boxMy =  boxMx/WIDTH, boxMy/HEIGHT  
        return boxMx, boxMy

    #duvara çarpma durumunu kontrol et
    def wall_check(self):
        if self.bomber.xcor() > 200 or self.bomber.xcor() < -200 or self.bomber.ycor() > 200 or self.bomber.ycor() < -200:
            self.reset_score()
            return True
    
    #tüm kutullar bitti mi
    def nobox_left_check(self):
        box_alive = 0
        for i in range(len(self.box)):
            if self.box_Exist[i]:
                box_alive += 1
        if box_alive == 0:        
            self.reset_score()
            return True
    
    def one_unit_away_box_check(self, boxHead):
        if self.bomber.xcor() == boxHead.xcor(): #vertical box detected
            if self.bomber.ycor() < boxHead.ycor(): #box above agent
                if abs(self.bomber.ycor() - boxHead.ycor()) <= UNIT_LENGTH :
                    return 'above' #directly box above agent
            elif self.bomber.ycor() >= boxHead.ycor(): #box below agent
                if abs(self.bomber.ycor() - boxHead.ycor()) <= UNIT_LENGTH:
                    return 'below' #directly box below agent
        elif self.bomber.ycor() == boxHead.ycor(): #horizontal box detected    
            if self.bomber.xcor() < boxHead.xcor(): #box right of agent
                if abs(self.bomber.xcor() - boxHead.xcor()) <= UNIT_LENGTH:
                    return 'right' #directly box right of agent
            elif self.bomber.xcor() >= boxHead.xcor(): #box left of agent
                if abs(self.bomber.xcor() - boxHead.xcor()) <= UNIT_LENGTH:
                    return 'left' #directly box left of agent
        return 'empty'
    
    def one_unit_away_bomb_check(self):
        if self.bomber.xcor() == self.bomb.xcor() and self.bomber.ycor() == self.bomb.ycor():
            return 'ontop'
        if self.bomber.xcor() == self.bomb.xcor(): #vertical box detected
            if self.bomber.ycor() < self.bomb.ycor(): #box above agent
                if abs(self.bomber.ycor() - self.bomb.ycor()) <= UNIT_LENGTH :
                    return 'above' #directly box above agent
            elif self.bomber.ycor() >= self.bomb.ycor(): #box below agent
                if abs(self.bomber.ycor() - self.bomb.ycor()) <= UNIT_LENGTH:
                    return 'below' #directly box below agent
        elif self.bomber.ycor() == self.bomb.ycor(): #horizontal box detected    
            if self.bomber.xcor() < self.bomb.xcor(): #box right of agent
                if abs(self.bomber.xcor() - self.bomb.xcor()) <= UNIT_LENGTH:
                    return 'right' #directly box right of agent
            elif self.bomber.xcor() >= self.bomb.xcor(): #box left of agent
                if abs(self.bomber.xcor() - self.bomb.xcor()) <= UNIT_LENGTH:
                    return 'left' #directly box left of agent
        return 'empty'
        
    def reset(self):
        if self.human:
            time.sleep(1) 
        self.bomber.goto(BOMBER_START_LOC_H, BOMBER_START_LOC_V)
        self.bomber.direction = 'stop'
        self.reward = 0
        self.total = 0
        self.done = False
        self.heart_beat_deposit = 800
        for i in range(len(self.box)):
            #print("box reset")
            self.box_Exist[i] = True
            self.box[i].goto(self.box_X[i],self.box_Y[i])

        state = self.get_state()

        return state


    def run_game(self):
        reward_given = False
        debug = False
        self.win.update()
        if self.keyPressed:
            self.move_bomber()
            if self.bomber.direction == "space" and self.bomb_planted:
                print("bomba dikemezsin")
                self.reward = -1
                reward_given = True
            self.keyPressed = False
            self.heart_beat_deposit -= 1 
            debug = debug_is_on
            #print(self.mass_center())
        #if self.be_exploded():
         #   self.reward = -100
         #   reward_given = True
        if self.collision:
            self.collision = False
            print("carptı")
            self.reward = -1
            reward_given = True
        if self.explode():#destroy box
            print("bomba patladı!")
            if not self.bomb_got_empty:
                for i in range(self.total - self.prev_score):
                    print("isabetli bomba!")
                    self.reward = 10
                    reward_given = True
                    self.heart_beat_deposit += 10 
            elif self.bomb_got_empty:
                print("bomba isabetsiz!")
                self.reward = -0.5
                reward_given = True
                self.bomb_got_empty = False
        if self.plant_warning and self.bomb_timer == 2:
            self.plant_warning = False
            self.reward = 0.25
            reward_given = True
            print("bomba yerlestirildi!")
        if self.heart_beat_deposit == 0:
            self.reward = -100
            reward_given = True
            self.done = True
            print("kalbi durdu!")
        self.measure_distance() #mass centere göre
        if self.wall_check():
            print("duvara çarptı!")
            self.reward = -100
            reward_given = True
            self.done = True
            if self.human:
                self.reset()
        if self.nobox_left_check():
            print("kutu kalmadı!")
            self.reward = 200
            reward_given = True
            self.done = True
            if self.human:
                self.reset()
        if not reward_given:
            if debug:
                print("ödülsüz hareket yapıldı!")
            if self.dist2 < self.prev_dist2:
                self.reward = 0
            else:
                self.reward = 0
        #eğitim zamanında bu gecikme kapalıdır
        #time.sleep(0.1)
        if self.human:
            time.sleep(SLEEP)
            state = self.get_state()
            if debug:
                print(state, self.reward, self.temporary)

    
    # AI agent openai gym step fonksiyonu
    def step(self, action):
        if action == 0:
            self.go_up()
        if action == 1:
            self.go_right()
        if action == 2:
            self.go_down()
        if action == 3:
            self.go_left()
        if action == 4:
            self.plant_bomb()
        self.run_game()
        state = self.get_state()
        return state, self.reward, self.done, {}


    def get_state(self):
        # bomber coordinates abs
        self.bomber.x, self.bomber.y = self.bomber.xcor()/WIDTH, self.bomber.ycor()/HEIGHT 
        #print(self.bomber.x, self.bomber.y)
        # bomber coordinates scaled 0-1
        self.bomber.xsc, self.bomber.ysc = self.bomber.x/WIDTH+0.5, self.bomber.y/HEIGHT+0.5
        
        self.massCenterX, self.massCenterY = self.mass_center()
        self.massCenterX, self.massCenterY = self.massCenterX/WIDTH, self.massCenterY/HEIGHT
        
        # wall check
        if self.bomber.y >= HEIGHT/2:
            wall_up, wall_down = 1, 0
        elif self.bomber.y <= -HEIGHT/2:
            wall_up, wall_down = 0, 1
        else:
            wall_up, wall_down = 0, 0
        if self.bomber.x >= WIDTH/2:
            wall_right, wall_left = 1, 0
        elif self.bomber.x <= -WIDTH/2:
            wall_right, wall_left = 0, 1
        else:
            wall_right, wall_left = 0, 0
        
        #box monitor
        test = [0,0,0,0, 0,0,0,0 ,0,0,0,0, 0,0,0,0] #ilk dortlu yakın kutu, ikinci dortlu yakın bomba, ucuncu dortlu yakin duvar, dorduncu dortlu en yakın neresinde
        #her dortlu icin [0,0,0,0] sirasiyla = up,right,down,left
        minDistance = 10000
        index = 0
        for i in range(len(self.box)):
                if self.box_Exist[i]:
                    #self.box[i].x, self.box[i].y = self.box[i].xcor()/WIDTH, self.box[i].ycor()/HEIGHT
                    temp = self.boxCollisionCheck(self.box[i])
                    if temp < minDistance:
                        minDistance = temp;
                        index = i
                    if self.one_unit_away_box_check(self.box[i]) == 'above':
                        test[0] = 1 #Bir ustunde kutu var
                    if self.one_unit_away_box_check(self.box[i]) == 'below':
                        test[2] = 1 #Bir altinda kutu var    
                    if self.one_unit_away_box_check(self.box[i]) == 'right':
                        test[1] = 1 #Bir saginda kutu var    
                    if self.one_unit_away_box_check(self.box[i]) == 'left':
                        test[3] = 1 #Bir solunda kutu var 
                        
        if self.one_unit_away_bomb_check() == 'above':
            test[4] = 1 #Bir ustunde bomba var
        if self.one_unit_away_bomb_check() == 'below':
            test[6] = 1 #Bir altinda bomba var
        if self.one_unit_away_bomb_check() == 'right':
            test[5] = 1 #Bir saginda bomba var
        if self.one_unit_away_bomb_check() == 'left':
            test[7] = 1 #Bir solunda bomba var
        if self.one_unit_away_bomb_check() == 'ontop':
            test[4] = 1 # Bombanın tam üstündeyiz
            test[5] = 1 
            test[6] = 1 
            test[7] = 1 
            
        test[8] = int(wall_up) 
        test[9] = int(wall_right)
        test[10] = int(wall_down)
        test[11] = int(wall_left)
        
        # test[8] = int(self.bomber.y >= self.massCenterY)#were above mass center
        # test[9] = int(self.bomber.x >= self.massCenterX)#were right of the mass center
        # test[10] = int(self.bomber.y < self.massCenterY)#were under mass center
        # test[11] = int(self.bomber.x < self.massCenterX)#were left of the mass center
        
        if self.box[index].ycor() - self.bomber.ycor() >= 20:
            test[12] = 1 #en yakin kutu ustunde
        elif self.bomber.ycor() - self.box[index].ycor() >= 20:
            test[14] = 1 #en yakin kutu altında
        if self.box[index].xcor() - self.bomber.xcor() >= 20:
            test[13] = 1 #en yakin kutu saginda
        elif self.bomber.xcor() - self.box[index].xcor() >= 20:
            test[15] = 1 #en yakin kutu solunda
        #print(f'index = {index}')
        self.temporary = index
        
        #print(test)
        #print(state)
        state = test
        return state

    def bye(self): 
        self.win.bye()


if __name__ == '__main__':            
    human = True
    env = Bomber(human=human)

    if human:#insan oyuncu için
        while True:
            env.run_game()

    

    



    
