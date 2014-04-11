import pygame, sys
import random
import copy
from pygame.locals import *
from operator import add,sub,mul

red = pygame.Color(255,0,0)
green = pygame.Color(0,255,0)
blue = pygame.Color(0,0,255)
black = pygame.Color(0,0,0)
white = pygame.Color(255,255,255)

def getx(vector):
	return vector[0]
def gety(vector):
	return vector[1]
def setx(vector,value):
	vector[0] = value
def sety(vector,value):
	vector[1] = value
def funcx(vector,function):
	vector[0] = function(vector[0])
def funcy(vector,function):
	vector[1] = function(vector[1])
def inside(m,a,b):
	return getx(a) <= getx(m) and gety(a) <= gety(m) and getx(m) < getx(b) and gety(m) < gety(b)
class Grid:
	def __init__(self, size):
		self.size = size
		self.grid = []
		self.entitygrid = []
		for i in range(getx(size)):
			self.grid.append([])
			self.entitygrid.append([])
			for j in range(gety(size)):
				self.grid[i].append(0)
				self.entitygrid[i].append([])
	def	updateEntityPosition(self, entity, sourcepos, destpos):
		if inside(destpos,[0,0],self.size):				
			self.entitygrid[getx(sourcepos)][gety(sourcepos)].remove(entity)
			self.entitygrid[getx(destpos)][gety(destpos)].append(entity)
			return True
		else:
			return False
	def getNeighbors(self, entity):
		neighbors = self.entitygrid[getx(entity.pos)][gety(entity.pos)]
		neighbors = copy.copy(neighbors)
		neighbors.remove(entity)
		return neighbors
	def getNearby(self, entity):
		dist = 10
		nearby = []
		i = 0
		for x in range(getx(entity.pos)-dist, getx(entity.pos)+dist+1):
			nearby.append([])
			for y in range(gety(entity.pos)-dist, gety(entity.pos)+dist+1):
				if not inside([x,y],[0,0],self.size):
					nearby[i].append([])
					continue
				entities = self.entitygrid[x][y]
				nearby[i].append(copy.copy(entities))
			i += 1
		return nearby, dist
	def deleteEntity(self, entity):
		self.entitygrid[getx(entity.pos)][gety(entity.pos)].remove(entity)
class Mover:
	def __init__(self, entity=None):
		self.entity = entity
		self.memory = []
		self.dir = [0,0]
		self.ret = True
		self.energy = 64
	def processNearby(self):
		dirdict = {(0,0):0, (1,0):1, (0,1):2, (-1,0):3, (0,-1):4}
		probs = [1,1,1,1,1]
		nearby, dist = self.entity.grid.getNearby(self.entity)
		for i in range(0,2*dist+1):
			for j in range(0,2*dist+1):
				entities = nearby[i][j]
				offsetx = i-dist
				offsety = j-dist
				if entities != [] and not (offsetx == 0 and offsety == 0):
					realdist = offsetx**2+offsety**2+1
					#realdist = abs(offsetx)+abs(offsety)+1
					if abs(offsetx) > abs(offsety):
						offsetx /= abs(offsetx)
						offsety = 0
					else:
						offsety /= abs(offsety)
						offsetx = 0
					if entities[0].name == "bad":
						probs[dirdict[(-offsetx,-offsety)]] += ((self.energy+1)*8192/(realdist*realdist)) #magic number: Neuronic impulse
					else:
						probs[dirdict[(offsetx,offsety)]] += int(4096/(realdist*realdist)) #magic number: Neuronic impulse
		maxprobs = max(probs)
		probs = [ maxprobs if x == maxprobs else x for x in probs]
		return probs
	def update(self,tick):
		if tick % 2 != 0:
			return
		if self.energy != 0:
			self.energy -= 1
			print self.energy
		dirdict = {(0,0):0, (1,0):1, (0,1):2, (-1,0):3, (0,-1):4}
		neighbors = self.entity.grid.getNeighbors(self.entity)
		for n in neighbors:
			if n.name == "apple":
				n.delete()
				self.energy += 16
			if n.name == "bad":
				print "I am in pain!"
		probability = self.processNearby()		
		if self.ret:
			if tuple(probability) == (1,1,1,1,1):
				probability[dirdict[tuple(self.dir)]] += 8
		if not self.ret:
			probability[dirdict[tuple(map(lambda x:-x, self.dir))]] += 8
		self.change(probability)		
		self.ret = self.entity.updatePosition(map(add,self.entity.pos,self.dir))
		
	def change(self,probability):
		print probability
		runningsum = [0]
		for p in probability:
			runningsum.append(runningsum[-1]+p)
		chosen = random.randint(0,runningsum[-1])
		for i in range(len(runningsum)):
			if runningsum[i] > chosen:
				self.dir = [[0,0],[1,0],[0,1],[-1,0],[0,-1]][i-1]
				break
class BadMover:
	def __init__(self, entity=None):
		self.entity = entity
	def update(self,tick):
		if tick % 640 == 0:
			#self.entity.delete()
			return
		if tick % 10 != 0:
			return
		dir = random.choice([[0,0],[1,0],[0,1],[-1,0],[0,-1]])
		self.entity.updatePosition(map(add,self.entity.pos,dir))

class Camera:
	def __init__(self, surface):
		self.surface = surface
	def drawGrid(self,grid):
		coords = [0,0]
		tilesize = 10
		for row in grid.grid:
			sety(coords,0)
			for tile in row:
				cameracoords = map(lambda a:a*tilesize, coords)
				pygame.draw.rect(self.surface,green,cameracoords+[tilesize,tilesize])
				funcy(coords,lambda a:a+1)
			funcx(coords,lambda a:a+1)
	def drawEntity(self,entity):
		cameracoords = map(lambda a:a*10, entity.pos)
		color = red
		if entity.sprite == "red":
			color = red
		elif entity.sprite == "blue":
			color = blue
		elif entity.sprite == "black":
			color = black
		pygame.draw.rect(self.surface,color,cameracoords+[10,10])
class Entity:
	def __init__(self,entitymanager,grid,pos=[0,0],sprite="red",name=None):
		self.parent = None
		self.pos = pos
		self.entitymanager = entitymanager
		self.name = name
		self.sprite = sprite
		self.grid = grid
		grid.entitygrid[getx(self.pos)][gety(self.pos)].append(self)
		self.mover = None
	def putMover(self):
		self.mover = Mover(self)
	def putBadMover(self):
		self.mover = BadMover(self)
	def updatePosition(self, pos):		
		ret = self.grid.updateEntityPosition(self,self.pos,pos)
		if not ret:
			return False
		self.pos = pos
		return True
	def delete(self):		
		self.grid.deleteEntity(self)
		self.entitymanager.deleteEntity(self)
class EntityManager:
	def __init__(self):
		self.grid = None
		self.camera = None
		self.entities = []
	def update(self,tick):
		for e in self.entities:
			if e.mover != None:
				e.mover.update(tick)
	def draw(self):
		self.camera.drawGrid(self.grid)
		for e in self.entities:
			self.camera.drawEntity(e)
	def deleteEntity(self,entity):
		self.entities.remove(entity)
	def makeFood(self,tick,coord=None):
		if tick % 60 != 0:
			return
		if coord == None:
			coord = [random.randint(0,63),random.randint(0,47)]
		food = Entity(self,self.grid,coord,sprite="red",name="apple")
		self.entities.append(food)
	def makeBad(self,tick):
		if tick % 60 != 0:
			return
		coord = [random.randint(0,63),random.randint(0,47)]
		bad = Entity(self,self.grid,coord,sprite="black",name="bad")
		bad.putBadMover()
		self.entities.append(bad)
	def doUserSpecific(self,surface):
		self.grid = Grid([64,48])
		self.player = Entity(self,self.grid,pos=[1,1],sprite="blue",name="player")
		self.player.putMover()
		self.entities.append(self.player)
		self.camera = Camera(surface)
		#self.makeFood(0,[1,2])
		#self.makeFood(0,[2,2])
		self.makeFood(0,[0,0])
		self.makeFood(0,[2,1])		
class Controller:
	def __init__(self, entitymanager):
		self.entitymanager = entitymanager
	def control(self,events):
		for event in events: #controller
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			if event.type == MOUSEMOTION:
				pass
				
class Game:
	def __init__(self):
		pygame.init()
		self.clock = pygame.time.Clock()
		self.tick = 0
	def start(self):
		surface = pygame.display.set_mode((640,480))
		pygame.display.set_caption("Feedback Game")
		entitymanager = EntityManager()
		entitymanager.doUserSpecific(surface)
		controller = Controller(entitymanager)
		while True:
			controller.control(pygame.event.get())
			entitymanager.update(self.tick) #model
			entitymanager.makeFood(self.tick)
			entitymanager.makeBad(self.tick)
			surface.fill(black)
			entitymanager.draw()
			pygame.display.update()
			self.clock.tick(60)
			self.tick += 1
Game().start()