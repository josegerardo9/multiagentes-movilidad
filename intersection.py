from mesa import Agent, Model
from mesa.space import SingleGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import numpy as np
import pandas as pd


def get_street(model):
    street = np.zeros((model.grid.width, model.grid.height), dtype='i, i')
    for cell in model.grid.coord_iter():
        cell_content, x, y = cell
        if isinstance(cell_content, Stoplight):
            street[x][y] = (cell_content.state, cell_content.unique_id)
        elif isinstance(cell_content, Car):
            street[x][y] = (4, cell_content.unique_id)

    # print(f"{street}\n")
    return street


class Car(Agent):
    # Car positions
    UP = 1  # Car starts up
    DOWN = 2  # Car starts down
    LEFT = 3  # Car starts left
    RIGHT = 4  # Car starts right

    num_of_cars_placed = 0

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.direction = None
        self.agent_placed = False
        self.passed_stoplight = False
        self.decided_turn = False
        self.car_stopped_by_red = False  # Check the color of the stoplight
        self.count = 0

        self.car_starting_pos = {
            # Y ES PRIMERO Y LUEGO X
            self.UP: (0, 4),  # Car UP position
            self.DOWN: (9, 5),  # Car DOWN position
            self.LEFT: (5, 0),  # Car LEFT position
            self.RIGHT: (4, 9)  # Car RIGHT position
        }
        self.place_agent()

    def place_agent(self):
        spawn = self.random.randint(1, 20)
        if spawn < 3:
            # We make a copy, so we can look no matter how many times
            copy_car_starting_pos = dict(self.car_starting_pos)
            # print(f"I am Agent {self.unique_id}, with possible positions: {copy_car_starting_pos}")# -> DEBUG
            # We choose the first position to try
            self.direction = self.random.choice(list(copy_car_starting_pos.items()))
            # We iterate over the positions in search of an empty cell
            while True:
                if not self.model.grid.is_cell_empty(self.direction[1]):  # If the cell we choose already has a car
                    # print(copy_car_starting_pos)# -> DEBUG
                    del copy_car_starting_pos[self.direction[0]]
                    # We delete the key (starting side) and value (starting coordinates) from the dictionary
                    if len(copy_car_starting_pos) != 0:  # If the dict is not empty
                        # We choose new coordinates
                        self.direction = self.random.choice(list(copy_car_starting_pos.items()))
                    else:  # The dict is empty
                        break
                else:  # We found an empty cell
                    # We delete the key (starting side) and value (starting coordinates) from the dictionary
                    del copy_car_starting_pos[self.direction[0]]
                    self.model.grid.place_agent(self, self.direction[1]) # We place the car agent
                    self.agent_placed = True # We now know this car is placed
                    self.count += 1
                    # print(f"Agent {self.unique_id} chose: {self.direction[1]}")# -> DEBUG
                    # print(f"Agent {self.unique_id} didn't choose: {copy_car_starting_pos}")# -> DEBUG
                    # print("------------------------------------------------------------------------")# -> DEBUG
                    break

    def step(self):
        # First check if car is placed
        if self.agent_placed:
            # The car agent has already been placed,
            # we now check if our car agent is in the last position of the grid or not
            if self.reached_end():
                # Car agent is in last position of the grid
                self.delete_agent()
            else:
                # We continue moving our car
                self.move()
        else:
            # If we couldn't add a car agent before, we will try again unless it has been placed 5 times
            if self.count < 5:
                # print(f"Times placed: {self.count}")
                self.place_agent()

    def move(self):
        # Move car
        if not self.passed_stoplight:
            self.check_for_stoplights()

        # not self.car_stopped_in_front and
        if not self.car_stopped_by_red and not self.check_cars_in_front():
            # We're moving
            if not self.decided_turn:
                self.turn_car()
            y, x = self.pos
            if self.direction[0] == self.UP:
                self.model.grid.move_agent(self, (y+1, x))
            elif self.direction[0] == self.DOWN:
                self.model.grid.move_agent(self, (y-1, x))
            elif self.direction[0] == self.LEFT:
                self.model.grid.move_agent(self, (y, x+1))
            elif self.direction[0] == self.RIGHT:
                self.model.grid.move_agent(self, (y, x-1))

    def reached_end(self):
        # If our car has reached one of these positions we return True
        car_ending_pos = [(9, 4), (0, 5), (5, 9), (4, 0)]
        for last_pos in range(4):
            if self.pos == car_ending_pos[last_pos]:
                return True
        return False

    def turn_car(self):
        turn_pos = {
            self.UP: (4, 4),  # Car starts up
            self.DOWN: (5, 5),  # Car starts down
            self.LEFT: (5, 4),  # Car starts left
            self.RIGHT: (4, 5)  # Car starts right
        }
        for key, value in turn_pos.items():
            if self.direction[0] == key and self.pos == value:
                turn = self.random.choice([True, False])  # We decide if the car turns or not
                self.decided_turn = True
                if turn:
                    self.decided_turn = True
                    if self.direction[0] == self.UP:
                        self.direction = list(self.car_starting_pos.items())[3]
                        # print(self.direction)
                    elif self.direction[0] == self.DOWN:
                        self.direction = list(self.car_starting_pos.items())[2]
                        # print(self.direction)
                    elif self.direction[0] == self.LEFT:
                        self.direction = list(self.car_starting_pos.items())[0]
                        # print(self.direction)
                    elif self.direction[0] == self.RIGHT:
                        self.direction = list(self.car_starting_pos.items())[1]
                        # print(self.direction)

    def check_for_stoplights(self):
        pos_stoplight = [(3, 3), (3, 6), (6, 3), (6, 6)]

        for position in pos_stoplight:
            y, x = position
            if (self.pos == (y, x+1) or self.pos == (y+1, x) or self.pos == (y, x-1) or self.pos == (y-1, x)) \
                    and isinstance(self.model.grid[y][x], Stoplight):
                # We detect a spotlight to our right
                stoplight = self.model.grid[y][x]
                if stoplight.state == Stoplight.GREEN or stoplight.state == Stoplight.YELLOW:
                    self.passed_stoplight = True
                    self.car_stopped_by_red = False
                elif stoplight.state == Stoplight.RED:
                    self.car_stopped_by_red = True

    def check_cars_in_front(self):
        neighbors = self.model.grid.get_neighbors(
            self.pos,
            moore=False,
            include_center=False
        )
        for neighbor in neighbors:
            y, x = neighbor.pos
            if ((self.direction[0] == self.UP and self.pos == (y - 1, x)) or
                (self.direction[0] == self.DOWN and self.pos == (y + 1, x)) or
                (self.direction[0] == self.LEFT and self.pos == (y, x - 1)) or
                (self.direction[0] == self.RIGHT and self.pos == (y, x + 1))) and \
                    isinstance(self.model.grid[y][x], Car):
                # If we detect a car in front of us
                return True
        return False

    def delete_agent(self):
        self.model.grid.remove_agent(self)  # We turn the agents position to None
        self.agent_placed = False
        self.passed_stoplight = False
        self.decided_turn = False
        self.car_stopped_by_red = False
        Car.num_of_cars_placed += 1


class Stoplight(Agent):
    GREEN = 1
    YELLOW = 2
    RED = 3
    pos_stoplight = [(3, 3), (3, 6), (6, 3), (6, 6)]
    pos_car_before_stoplight = [(2, 4), (4, 7), (5, 2), (7, 5)]
    first_positions = [(3, 3), (6, 6)]
    second_positions = [(3, 6), (6, 3)]
    first_position_on = False
    second_position_on = False
    first_car = False

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = self.YELLOW

    def step(self):
        # Control the light of the stoplight
        # print(self.first_car)
        if not self.first_car:
            self.start_sequence()
        else:
            self.control_light()

    def advance(self):
        pass

    def start_sequence(self):
        for position in range(4):
            y, x = self.pos_car_before_stoplight[position]
            if self.pos == self.pos_stoplight[position] and isinstance(self.model.grid[y][x], Car):
                # If we are in this position and a car is right,
                # we now turn the first stoplights green and the others red
                if self.pos_stoplight[position] in self.first_positions:
                    # LEFT-UP and DOWN-RIGHT stoplights turn green
                    # LEFT-RIGHT and DOWN-LEFT stoplights turn red
                    for g_position in self.first_positions:
                        g_y, g_x = g_position
                        self.model.grid[g_y][g_x].state = self.GREEN
                    for r_position in self.second_positions:
                        r_y, r_x = r_position
                        self.model.grid[r_y][r_x].state = self.RED
                    self.first_position_on = True
                    self.second_position_on = False
                else:
                    # LEFT-UP and DOWN-RIGHT stoplights turn red
                    # LEFT-RIGHT and DOWN-LEFT stoplights turn green
                    for g_position in self.first_positions:
                        g_y, g_x = g_position
                        self.model.grid[g_y][g_x].state = self.RED
                    for r_position in self.second_positions:
                        r_y, r_x = r_position
                        self.model.grid[r_y][r_x].state = self.GREEN
                    self.first_position_on = False
                    self.second_position_on = True

                Stoplight.first_car = True
                self.model.steps_counter = 1
                break

    def control_light(self):
        if self.model.steps_counter == 1:
            if self.first_position_on:
                for g_position in self.first_positions:
                    g_y, g_x = g_position
                    self.model.grid[g_y][g_x].state = self.GREEN
                for r_position in self.second_positions:
                    r_y, r_x = r_position
                    self.model.grid[r_y][r_x].state = self.RED
            elif self.second_position_on:
                for g_position in self.first_positions:
                    g_y, g_x = g_position
                    self.model.grid[g_y][g_x].state = self.RED
                for r_position in self.second_positions:
                    r_y, r_x = r_position
                    self.model.grid[r_y][r_x].state = self.GREEN
        elif self.model.steps_counter == 9:
            if self.first_position_on:
                for position in self.first_positions:
                    y, x = position
                    self.model.grid[y][x].state = self.YELLOW
            elif self.second_position_on:
                for position in self.second_positions:
                    y, x = position
                    self.model.grid[y][x].state = self.YELLOW
        elif self.model.steps_counter == 11:
            if self.first_position_on:
                self.first_position_on = False
                self.second_position_on = True
            elif self.second_position_on:
                self.first_position_on = True
                self.second_position_on = False


class Street(Model):
    # Stoplight Positions
    pos_stoplight = [(3, 3), (3, 6), (6, 3), (6, 6)]

    def __init__(self, width, height, num_cars):
        self.grid = SingleGrid(width=width, height=height, torus=True)
        self.num_cars = num_cars
        self.schedule = SimultaneousActivation(self)
        self.steps_counter = 1
        self.total_cars = self.num_cars * 5

        # We create first the stoplights
        for stoplight in range(len(self.pos_stoplight)):
            a = Stoplight(stoplight+1, self)
            self.schedule.add(a)

            # Add the stoplight to a designated position
            # print(self.pos_stoplight[stoplight])
            self.grid.place_agent(a, self.pos_stoplight[stoplight])

        # We create the cars
        for car in range(self.num_cars):
            a = Car(car+5, self)
            self.schedule.add(a)

        self.datacollector = DataCollector(
            model_reporters={'Street': get_street}
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        if self.steps_counter > 10:
            self.steps_counter = 1
        else:
            self.steps_counter += 1

    def no_more_cars(self):
        if Car.num_of_cars_placed >= self.total_cars:
            return True
        return False


# Number of cars that appear
NUM_CARS = 10

models = Street(width=10, height=10, num_cars=NUM_CARS)

while not models.no_more_cars():
    models.step()

all_streets = models.datacollector.get_model_vars_dataframe()
