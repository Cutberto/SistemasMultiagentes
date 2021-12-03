# TC2008B. Sistemas Multiagentes y Gráficas Computacionales
# Python server to interact with Unity
# Sergio. Julio 2021

from http.server import BaseHTTPRequestHandler, HTTPServer
 

import json, logging, os, atexit

    # La clase `Model` se hace cargo de los atributos a nivel del modelo, maneja los agentes. 
    # Cada modelo puede contener múltiples agentes y todos ellos son instancias de la clase `Agent`.
from mesa import Agent, Model 

    # Debido a que necesitamos un solo agente por celda elegimos `SingleGrid` que fuerza un solo objeto por celda.
from mesa.space import MultiGrid

    # Con `SimultaneousActivation` hacemos que todos los agentes se activen de manera simultanea.
from mesa.time import SimultaneousActivation

    # Vamos a hacer uso de `DataCollector` para obtener el grid completo cada paso (o generación) y lo usaremos para graficarlo.
from mesa.datacollection import DataCollector


import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

import numpy as np
import pandas as pd
import random

import time
import datetime
 
import numpy as np
from boid import Boid

# Size of the board:
width = 30
height = 30

# Set the number of agents here:
flock = [Boid(*np.random.rand(2)*30, width, height) for _ in range(20)]

def updatePositions():
    global flock
    positions = []
    for boid in flock:
        boid.apply_behaviour(flock)
        boid.update()
        pos = boid.edges()
        positions.append(pos)
    return positions

def positionsToJSON(ps):
    posDICT = []
    for p in ps:
        pos = {
            "x" : p[0],
            "z" : p[1],
            "y" : p[2]
        }
        posDICT.append(pos)
    return json.dumps(posDICT)



def obtener_calle(model):
    grid = np.zeros((model.grid.width, model.grid.height))
    #Aqui se asignas los colores de las celdas del grid para la visualizacion de la simulacion =D muito bonito, joga bonito
    for cell in model.grid.coord_iter():
        cell_content, x, y = cell
        for content in cell_content:
            if isinstance(content,car):  
                grid[x][y] = 30  #color azul para el auto
            elif isinstance(content,Banqueta): 
                grid[x][y] = 100 #color blanco de la calle (bordes) 
            elif isinstance (content, sensores):
                grid[x][y] = 10 #color morado de los sensores
            elif isinstance(content, Semaforo):
                if content.estado_luz == 0: 
                    grid[x][y] = 60 #color verde de semaforo
                elif content.estado_luz == 1:
                    grid[x][y] = 90 #color rojo de semaforo 
               
            else: 
                grid[x][y] = 0  #color default del fondo 
    return grid


# In[104]:


#semaforo
class Semaforo(Agent): #modelacion de los carritos muito bonitos
    
    def __init__(self, unique_id,  Turno,  color, model):
        super().__init__(unique_id,model)
        self.Turno = Turno ## indica si es el turno de que el carro avance o no :3
        self.estado_luz = color # 0 es pasa, 1 para 

    def step(self): 
        if self.Turno == self.model.roadTurn: 
            self.estado_luz = 0 
        else: 
            self.estado_luz = 1

        tempDict =[self.unique_id, self.estado_luz]
        
        try: 
            semFrameAct =self.model.coloresSemaforos[self.model.frame]
            semFrameAct.append([self.unique_id, self.estado_luz] )
            self.model.coloresSemaforos[self.model.frame] = semFrameAct
        except:#si es el primer carro del frame
            
            self.model.coloresSemaforos.append(tempDict)
        


# In[105]:


#modelacion de los sensores de carros

class sensores(Agent): #modelacion de sensores que detectas vehiculos 
    def __init__(self,unique_id, number, model):
        super().__init__(unique_id,model)
        self.hasCar = False
        self.counter = 0
        self.myLight = number  

    
#    def changeTurn(self):
#        if self.model.roadTurn == 0:
#            self.model.roadTurn = 1
#        elif self.model.roadTurn == 1:
#            self.model.roadTurn = 0 
    
    def changeTurn(self):
        if self.model.roadTurn == 0:
            self.model.roadTurn = 1
        elif self.model.roadTurn == 1:
            self.model.roadTurn = 2 
        elif self.model.roadTurn == 2:
            self.model.roadTurn = 3
        elif self.model.roadTurn == 3:
            self.model.roadTurn = 0 
  


# In[106]:



class Banqueta(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id,model)

        


# In[107]:

#agente carro 
        
class car(Agent):
    def __init__(self, unique_id, direction ,pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.direction = direction # 0 izquierda, 1 derecha, 2 arriba, 3 abajo 
        self.stop = False
        self.spawnDirection = direction
        self.crossed = False
        self.eliminated = False
    def getNextMove(self):
        
        
        
        #Primero guardamos la posicion actual para mandarla a unity
        tempDict = [self.unique_id, self.pos]
        self.model.posicionesCarros.append(tempDict)
      #  try: 
      #      carrosFrameAct = self.model.posicionesCarros[0]
      #      carrosFrameAct.append([self.unique_id, self.pos] )
      #      self.model.posicionesCarros[self.model.frame] = carrosFrameAct
      #  except:#si es el primer carro del frame
      #      
      #      self.model.posicionesCarros = tempDict
        
        
        
        ##
        ##Esta parte del codigo es para que los carros tomen la decision de si van a dar
        ##la vuelta al cruzar la esquina o si no la van a dar
        ## Ademas aqui el carro avisa si ya cruzo para que el semaforo lo tenga en cuenta
        ##
        ##
        
        
        
        #si ya cruzaste el semaforo y vas hacia la derecha :
        if self.pos[1] == 6 and self.direction == 1 and self.stop == False:
            decision = random.randint(0,2) #solo hay 1/3 de posibilidad de que el carro gire
            if (decision == 1): #aqui decide de manera random si el carro va a girar o no
                    #los de la derecha giran hacia abajo
                self.direction = 3
            self.model.carsWaiting0 -=1 #cars0 son los carros hacia la derecha 
             
        #si vas hacia la izquierda y ya cruzaste :
        if self.pos[1] == 8 and self.direction == 0 and self.stop == False:
            decision = random.randint(0,2)
            if (decision == 1): #aqui decide de manera random si el carro va a girar o no
                    #los de la derecha giran hacia arriba
                self.direction = 2
            self.model.carsWaiting2 -=1 #cars2 son los carros hacia la izquierda 

        #si vas hacia arriba :
        if self.pos[0] == 8 and self.direction == 2 and self.stop == False:
            decision = random.randint(0,2)
            if (decision == 1): #aqui decide de manera random si el carro va a girar o no
                    #los de arriba giran hacia la derecha
                self.direction = 1
            self.model.carsWaiting1 -=1 #cars1 son los carros hacia arriba 

        #si vas hacia abajo :  
        if self.pos[0] == 6 and self.direction == 3 and self.stop == False:
            decision = random.randint(0,2)
            if (decision == 1): #aqui decide de manera random si el carro va a girar o no
                    #los de abajo giran hacia la izquierda
                self.direction = 0
            self.model.carsWaiting3 -=1 #cars3 son los carros hacia abajo 
        
        
        
        ##
        ##Esta parte del codigo es para deletear los agentes, especificamente agregarlos a la lista de removes
        ##El carro se agrega a la lista de delete cuando esta a un paso de llegar al final de la calle, asi 
        ##hara que en el siguiente paso llegue al final y en seguida sea removido por parte del step de Interseccion =)
        ##
        
        
        
        
        
        #si llegaste al final y vas hacia la derecha :
        if self.pos[1] == model.width -2 and self.direction == 1 and self.eliminated == False:
            #nextPos = (self.pos[0],0)
            #return nextPos
            #self.model.grid.remove_agent(self)
            self.model.carsToRemove.append(self)
            #return (0,0)
        #si vas hacia la izquierda :
        if self.pos[1] == 1 and self.direction == 0 and self.eliminated == False:
            #nextPos = (self.pos[0],model.width - 1)
            #return nextPos
            self.model.carsToRemove.append(self)

        #si vas hacia arriba :
        if self.pos[0] == 1 and self.direction == 2 and self.eliminated == False:
            #nextPos = (model.height-1,self.pos[1])
            #return nextPos
            self.model.carsToRemove.append(self)
        #si vas hacia abajo :  NOTA: esto causaba un bug cuando era model.height - 2
        if self.pos[0] == model.height -3 and self.direction == 3 and self.eliminated == False:
            #nextPos = (0,self.pos[1])
            #return nextPos
            self.model.carsToRemove.append(self)
        
        ## aqui falta poner las condiciones de fin para las demas direcciones !!!!!!!!!!!!!!!!!!! sos
        
        nextPos = (0,0)
        if self.crossed == False: #si el carro no ha cruzado el semaforo
            if self.direction == 0: #avanza a la direccion correspondienTec
                nextPos = (self.pos[0], self.pos[1] - 1)
            elif self.direction == 1:
                nextPos = (self.pos[0], self.pos[1] + 1)
            elif self.direction == 2:
                nextPos = (self.pos[0] -1 , self.pos[1])
            elif self.direction == 3:
                nextPos = (self.pos[0] + 1, self.pos[1])
        else: #si ya cruzo
            pass ## aqui poner que pasa si no ha cruzado
        return nextPos
    
    
    
    def drive(self):
        if self.eliminated == False:
            thisCell = self.model.grid.get_cell_list_contents([self.pos])
            isLC = len([obj for obj in thisCell if isinstance(obj,sensores)])
            if isLC > 0:

              #checamos hacia donde se dirigen para decirle a cual semaforo deben obedecer 
            # 0 izquierda, 1 derecha, 2 arriba, 3 abajo 
                if self.direction == 0:
                    thisOtherCell = self.model.grid.get_cell_list_contents([(7,5)])
                    light_object = [obj for obj in thisOtherCell if isinstance(obj, Semaforo)]

                if self.direction == 1:
                    thisOtherCell = self.model.grid.get_cell_list_contents([(7,9)])
                    light_object = [obj for obj in thisOtherCell if isinstance(obj, Semaforo)]
                if self.direction == 2:
                    thisOtherCell = self.model.grid.get_cell_list_contents([(5,7)])
                    light_object = [obj for obj in thisOtherCell if isinstance(obj, Semaforo)]

                if self.direction ==3:
                    thisOtherCell = self.model.grid.get_cell_list_contents([(9,7)])
                    light_object = [obj for obj in thisOtherCell if isinstance(obj, Semaforo)]



              #ahora checamos el semaforo
                if light_object[0].estado_luz == 1:
                    self.stop = True
                else: self.stop = False

            if not self.stop and not self.eliminated:
                nextPos = self.getNextMove()
                #thisCell = self.model.grid.get_cell_list_contents([nextPos])
                #howManyCars = len([obj for obj in thisCell if isinstance(obj,car)])
                if validPos( nextPos[1],nextPos[0], self.model.width, self.model.height, self.direction) == True: #solo se mueve si su nextpos es valida
                    thisCell = self.model.grid.get_cell_list_contents([nextPos])
                    howManyCars = len([obj for obj in thisCell if isinstance(obj,car)])
                    if howManyCars == 0:
                        self.model.grid.move_agent(self,nextPos)
            else: 
                tempDict = [self.unique_id, self.pos]
                self.model.posicionesCarros.append(tempDict)
        else:
            tempDict = [self.unique_id, (0,0)]
            self.model.posicionesCarros.append(tempDict)
            
    def step(self):
        
        self.drive()
        
def validPos( x,y, width, height, direction):
    if x > width -1 and direction == 1:
        return False
        #si vas hacia la izquierda :
    if x < 1 and direction == 0:
        return False
        #si vas hacia arriba :
    if y < 1 and direction == 2:
        return False
        #si vas hacia abajo :  NOTA: esto causaba un bug cuando era model.height - 2
    if y > height -1 and direction == 3:
        return False
    return True

# In[108]:





class Interseccion_calle(Model):
     def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, True)
        self.schedule = SimultaneousActivation(self)
        self.roadTurn = 0 # 0 a 1 en este caso
        #inicializamos los objetos
        counterX = 0
        y_v = 5
        self.carsToRemove=[]
        self.spawnCar =[]
        self.frame = 0
        #conteo de carros totales para control de spawn
        self.carCount0 = 0
        self.carCount1 = 0
        self.carCount2 = 0
        self.carCount3 = 0
        self.coolDown = False
        
        #conteo de carros en espera para IA del semaforo
        self.carsWaiting0 = 0
        self.carsWaiting1 = 0
        self.carsWaiting2 = 0
        self.carsWaiting3 = 0
        
        #cooldown para cambio de semaforo
        self.coolDown_time = 0
        
        #lista para mandar datos a unity
        self.posicionesCarros =[]
        self.coloresSemaforos=[]
         
        
#aqui se construte el escenario
        for h in range (width):
            for k in range(height):
                if h == 5 and (k < 5 or k > height - 6 ):
                    varB = Banqueta(h+700,self)
                    self.grid.place_agent(varB,(k,h))

                if h == 9 and (k < 5 or k > height - 6 ):
                    varC = Banqueta(h+600,self)
                    self.grid.place_agent(varC,(k,h))
      
        for i in range (12):
            if i == 6:
                counterX = 0
                y_v = 9
            z = Banqueta(i,self)
            self.schedule.add(z)
            self.grid.place_agent(z,(y_v,counterX))
            counterX += 1
         
        counterX = 9
        y_v = 5

        for j in range (12):
            if j == 6:
                counterX = 9
                y_v =  9
            var = Banqueta(j+100, self)
            self.schedule.add(var)
            self.grid.place_agent(var,(y_v, counterX))
            counterX += 1 
        
#aqui es donde spawnean los carros como tal
        
        #crear  lightChecks en sus posiciones respectivas
        
        #este corresponde al semaforo de la izquierda, o sea esta colocado en la derecha (Enfrente de su semaforo)
        lc_izq = sensores(900, 0, self)
        self.schedule.add(lc_izq)
        self.grid.place_agent(lc_izq,(8,5)) #ESTO TIENE LAS X Y ALREVES AWAAS!!!
        

        lc_arriba = sensores(901, 1, self)
        self.schedule.add(lc_arriba)
        self.grid.place_agent(lc_arriba,(9,8))
        
        lc_abajo = sensores(902, 1, self)
        self.schedule.add(lc_abajo)
        self.grid.place_agent(lc_abajo,(5,6))

        lc_der = sensores(903, 0, self)
        self.schedule.add(lc_der)
        self.grid.place_agent(lc_der,(6,9))
        
        #crear   semaforos en sus posiciones respectivas     
        #el orden de encendido original era  0 1 1 0 
        semaforo_izquierda = Semaforo(510,0,2,self)
        self.schedule.add(semaforo_izquierda)
        self.grid.place_agent(semaforo_izquierda,(7,9)) #X Y AL REVES OTRA VEZ =)

        semaforo_arriba = Semaforo(511,1,2,self)
        self.schedule.add(semaforo_arriba)
        self.grid.place_agent(semaforo_arriba,(5,7))
        
        semaforo_abajo = Semaforo(512,2,2,self)
        self.schedule.add(semaforo_abajo)
        self.grid.place_agent(semaforo_abajo,(9,7))
        
        semaforo_derecha = Semaforo(513,3,2,self)
        self.schedule.add(semaforo_derecha)
        self.grid.place_agent(semaforo_derecha,(7,5))

        # Aquí definimos con colector para obtener el grid completo.
        self.datacollector = DataCollector(model_reporters={"Grid": obtener_calle})
   

     def step(self) :
        self.posicionesCarros = [] #esto es para que solo se mande 1 frame a la vez
        self.coloresSemaforos = []
        #self.datacollector.collect(self)     
        #ciclo para remover a todos los carros que salen de la pantalla
        self.carsToRemove = list(set(self.carsToRemove))
        for c in self.carsToRemove:
            if c is not None:
                if c.spawnDirection == 1:
                    self.carCount0 -=1
                elif c.spawnDirection == 2:
                    self.carCount1 -=1
                elif c.spawnDirection == 0:
                    self.carCount2 -=1
                elif c.spawnDirection == 3:
                    self.carCount3 -=1


                self.grid.remove_agent(c)
                #self.schedule.remove(c)
                c.eliminated = True
                self.carsToRemove.remove(c)

        
       
        
        
        
        
       
        x = 0
        y = 0

        ##
        ## Aqui se spawnean carros de manera aleatoria. se decide si 
        ## en este frame va a spawnear carro con probabilidad de 50% 
        ## (si el limite de carros por carril aun no se alcanza)
        ## Se establece un cooldown de 1 frame entre cada posible spawneo
        ## 
        
        decision = random.randint(0,1)
        randCar = random.randint(0,3)
        carsAmount = 4
        if (decision == 1 and self.coolDown == False):
            if (randCar == 0 and self.carCount0 < carsAmount):
                x = 8
                y = 0
                b = car((self.frame + 20, self.frame + 200), 1,(0,0),self)
                
                self.grid.place_agent(b,(x,y))
                self.schedule.add(b)
                self.carCount0 += 1
                self.carsWaiting0+= 1
            elif (randCar == 1 and self.carCount1 < carsAmount):
                x = 14
                y = 8
                b2 = car((self.frame + 20, self.frame + 201),2,(0,0),self) #carro abajo
                
                self.grid.place_agent(b2,(14,8))
                
                self.schedule.add(b2)
                self.carCount1 += 1
                self.carsWaiting1+= 1
                
            elif (randCar == 2 and self.carCount2 < carsAmount): #carros de la derecha
                y = 6
                x = 14
                b3 = car((self.frame + 20, self.frame + 202),0,(0,0),self)
                
                self.grid.place_agent(b3,(6,14))
                self.schedule.add(b3)
                self.carCount2 +=1
                self.carsWaiting2+= 1
                
            elif (randCar == 3 and self.carCount3 < carsAmount):
                x = 0
                y = 6
                b4 = car((self.frame + 20, self.frame + 203),3,(0,0),self) #carrp arriba
                
                self.grid.place_agent(b4,(0,6))
                self.schedule.add(b4)
                self.carCount3 +=1
                self.carsWaiting3 += 1
            self.coolDown = True
        else:
            self.coolDown = False 
        ##############################################
        ##
        ##  Se realiza una subasta para ver a que carril ceder el turno.  
        ##  Existe un tiempo de cooldown de 2 steps minimos de duracion de cada luz, 
        ##  Si el semaforo acaba de cambiar, no puede volver a cambiar hasta dos frames 
        ##  despues, esto para evitar cambios abruptos 
        ##############################################
        
        chosen_light = None
        #cantidad de frames que se debe esperar entre un cambio de luz y otro 
        COOLFRAMES = 3
        #se busca cual es el carril con mas carros esperando a pasar
        most_cars = 0 

        if (self.carsWaiting0 >= most_cars):
            most_cars = self.carsWaiting0
        if (self.carsWaiting1 >= most_cars):
            most_cars = self.carsWaiting1
        if (self.carsWaiting2 >= most_cars):
            most_cars = self.carsWaiting2
        if (self.carsWaiting3 >= most_cars):
            most_cars = self.carsWaiting3
        #revisa cual fue elegido para despues ver si se puede ceder el turno al carril (por el cooldown)
        if (self.carsWaiting0 == most_cars and self.coolDown_time ==0):
            #aqui se cede el turno
            self.roadTurn = 0 #prende el semaforo para los carros q van hacia la derecha
            self.coolDown_time = COOLFRAMES

        elif (self.carsWaiting1 == most_cars and self.coolDown_time ==0):
            #aqui se cede el turno
            self.roadTurn = 1 #prende el semaforo para los carros q van hacia arriba
            self.coolDown_time = COOLFRAMES

        elif (self.carsWaiting2 == most_cars and self.coolDown_time ==0):
            #aqui se cede el turno
            self.roadTurn = 3 #prende el semaforo para los carros q van hacia la izq
            self.coolDown_time = COOLFRAMES

        elif (self.carsWaiting3 == most_cars and self.coolDown_time ==0):
            #aqui se cede el turno
            self.roadTurn = 2 #prende el semaforo para los carros q van hacia  abajo
            self.coolDown_time = COOLFRAMES
        else:
            self.coolDown_time -=1 #reduce el cooldown hasta que llegue a 0 y pueda volver a cambiar turno

        
        
        self.datacollector.collect(self)   
        self.schedule.step()
        self.frame += 1
              #print(self.posicionesCarros)
        #self.datacollector.collect(self)   
        


M = 15

N = 15

MAX_TIME = 0.1

start_time = time.time()
model = Interseccion_calle(M, N)

#while((time.time() - start_time) < MAX_TIME):
#    model.step()

 

def posToJson(posicionesCarros):
    Dict = []
    for position in posicionesCarros:
        pos = {
            "x" : position[1][0],
            "y" : 0,
            "z" : position[1][1]
        }
        Dict.append(pos)
    return json.dumps(Dict)

def actualizar():
    model.step()
    car_positions = model.posicionesCarros
    json = posToJson(car_positions)
    print(json)
    return json

 

all_grid = model.datacollector.get_model_vars_dataframe()
#print ("Pos carros")

class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        #post_data = self.rfile.read(content_length)
        post_data = json.loads(self.rfile.read(content_length))
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     #str(self.path), str(self.headers), post_data.decode('utf-8'))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), json.dumps(post_data))
        
        '''
        x = post_data['x'] * 2
        y = post_data['y'] * 2
        z = post_data['z'] * 2
        
        position = {
            "x" : x,
            "y" : y,
            "z" : z
        }

        self._set_response()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        self.wfile.write(str(position).encode('utf-8'))
        '''
        
      #  positions = updatePositions()
        positions = actualizar()
        print("Posiciones de actualizar() : ")
        print(positions)
        self._set_response()
        resp = "{\"data\":" + positions + "}"
        #print(resp)
        self.wfile.write(resp.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL+C stops the server
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")

if __name__ == '__main__':
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
