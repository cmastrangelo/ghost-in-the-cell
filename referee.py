import random
import matplotlib.pyplot as plt
import numpy as np


class Visualizer:
    def __init__(self, game):
        self.game = game

    def visualize(self):
        fig, ax = plt.subplots()

        # Initialize factories positions (this is a heuristic and might not reflect actual distances)
        positions = self.generate_positions()

        # Plot links
        for (f1, f2), distance in self.game.distances.items():
            x1, y1 = positions[f1]
            x2, y2 = positions[f2]
            ax.plot([x1, x2], [y1, y2], "k-", lw=1, alpha=0.6)  # Draw links
            # Optionally, annotate the distance
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(
                mid_x, mid_y, str(distance), color="purple", fontsize=8, ha="center"
            )

        # Plot factories
        for i, factory in enumerate(self.game.factories):
            x, y = positions[i]
            color = (
                "grey"
                if factory.owner == 0
                else "blue"
                if factory.owner == 1
                else "red"
            )
            ax.scatter(x, y, c=color, s=100, edgecolors="black")
            ax.text(
                x, y, f"{i}\n{factory.cyborgs}", color="black", ha="center", va="center"
            )

        # Plot troops
        for troop in self.game.troops:
            x_source, y_source = positions[troop.source_factory]
            x_destination, y_destination = positions[troop.destination_factory]
            total_travel_time = self.game.distances.get(
                (troop.source_factory, troop.destination_factory), 20
            )
            progress = (total_travel_time - troop.travel_time) / total_travel_time
            x_troop = x_source + (x_destination - x_source) * progress
            y_troop = y_source + (y_destination - y_source) * progress
            color = "blue" if troop.owner == 1 else "red"
            ax.scatter(
                x_troop, y_troop, c=color, s=50, edgecolors="black", marker="^"
            )  # Plot troop as a triangle
            ax.text(
                x_troop,
                y_troop,
                f"{troop.num_cyborgs}",
                color="black",
                ha="center",
                va="center",
            )

        # Plot bombs
        for bomb in self.game.bombs:
            x_source, y_source = positions[bomb.source_factory]
            x_destination, y_destination = positions[bomb.destination_factory]
            total_travel_time = self.game.distances.get(
                (bomb.source_factory, bomb.destination_factory), 20
            )
            progress = (total_travel_time - bomb.travel_time) / total_travel_time
            x_bomb = x_source + (x_destination - x_source) * progress
            y_bomb = y_source + (y_destination - y_source) * progress
            color = "blue" if bomb.owner == 1 else "red"
            ax.scatter(
                x_bomb, y_bomb, c=color, s=50, edgecolors="black", marker="*"
            )  # Plot bomb as a star

        ax.axis("equal")  # Set equal scaling by changing axis limits
        plt.title("Game State Visualization")
        plt.show()

    def generate_positions(self):
        # A simple heuristic approach to distribute factories in 2D space
        angle_step = 360 / len(self.game.factories)
        positions = {}
        radius = 10  # Radius of the circle on which factories are placed
        for i in range(len(self.game.factories)):
            angle = np.deg2rad(angle_step * i)
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            positions[i] = (x, y)
        return positions


class Bomb:
    def __init__(self, owner, source_factory, destination_factory, travel_time):
        self.owner = owner
        self.source_factory = source_factory
        self.destination_factory = destination_factory
        self.travel_time = travel_time


class Factory:
    def __init__(self, owner, cyborgs):
        self.owner = owner  # 0 for neutral, 1 for player 1, 2 for player 2
        self.cyborgs = cyborgs
        # Production rate is now variable between 0 and 3 for non-neutral factories
        self.production = random.randint(0, 3) if owner != 0 else 0
        self.production_disabled = False


class Troop:
    def __init__(
        self, owner, num_cyborgs, source_factory, destination_factory, travel_time
    ):
        self.owner = owner
        self.num_cyborgs = num_cyborgs
        self.source_factory = source_factory
        self.destination_factory = destination_factory
        self.travel_time = travel_time


class Game:
    def __init__(self, factory_count, link_count):
        self.factories = []
        self.troops = []
        self.bombs = []
        self.distances = {}
        self.initialize_factories(factory_count)
        self.initialize_distances(factory_count, link_count)

    def initialize_factories(self, factory_count):
        for _ in range(factory_count):
            self.factories.append(
                Factory(0, random.randint(15, 30))
            )  # Neutral factories
        # Assign initial factories to players
        self.factories[0].owner, self.factories[0].production = 1, random.randint(0, 3)
        self.factories[1].owner, self.factories[1].production = 2, random.randint(0, 3)

    def initialize_distances(self, factory_count, link_count):
        # Simulate links and distances based on the provided constraints
        links = set()
        while len(links) < 2 * link_count:
            f1, f2 = random.sample(range(factory_count), 2)
            if (f1, f2) not in links and (f2, f1) not in links:
                distance = random.randint(1, 20)
                self.distances[(f1, f2)] = distance
                self.distances[(f2, f1)] = distance  # Ensure symmetry
                links.add((f1, f2))

    def send_troop(self, owner, num_cyborgs, source_factory, destination_factory):
        if self.factories[source_factory].owner != owner:
            raise ValueError("You do not own the source factory.")
        travel_time = self.distances.get((source_factory, destination_factory), 20)
        self.troops.append(
            Troop(owner, num_cyborgs, source_factory, destination_factory, travel_time)
        )
        self.factories[source_factory].cyborgs -= num_cyborgs

    def send_bomb(self, owner, source_factory, destination_factory):
        if self.factories[source_factory].owner != owner:
            raise ValueError("You do not own the source factory.")
        travel_time = self.distances.get((source_factory, destination_factory), 20)
        self.bombs.append(Bomb(owner, source_factory, destination_factory, travel_time))

    def update(self):
        # Move existing troops and prepare for battles
        self.update_troops()

        # Update bombs
        self.update_bombs()

        # Produce new cyborgs in all factories
        for factory in self.factories:
            if (
                factory.owner != 0 and factory.production_disabled == 0
            ):  # Neutral factories do not produce
                factory.cyborgs += factory.production
            elif factory.production_disabled > 0:
                factory.production_disabled -= (
                    1  # Decrease the production disabled counter
                )

    def update_troops(self):
        battles = {}  # Dictionary to organize battles by destination factory
        for troop in self.troops[:]:
            troop.travel_time -= 1
            if troop.travel_time == 0:
                dest = troop.destination_factory
                if dest not in battles:
                    battles[dest] = []
                battles[dest].append(troop)
                self.troops.remove(troop)

        # Now, solve battles
        for dest, troops in battles.items():
            self.resolve_battle(dest, troops)

    def update_bombs(self):
        # Similar to previous bomb update implementation
        for bomb in self.bombs[:]:
            bomb.travel_time -= 1
            if bomb.travel_time == 0:
                self.resolve_bomb(bomb)
                self.bombs.remove(bomb)

    def resolve_bomb(self, bomb):
        factory = self.factories[bomb.destination_factory]
        destroyed_cyborgs = max(10, factory.cyborgs // 2)
        factory.cyborgs -= destroyed_cyborgs
        factory.production_disabled = 5  # Disable production for 5 turns

    def resolve_battle(self, destination_factory, arriving_troops):
        # Group arriving troops by owner
        combatants = {}
        for troop in arriving_troops:
            if troop.owner not in combatants:
                combatants[troop.owner] = 0
            combatants[troop.owner] += troop.num_cyborgs

        # Determine the outcome of battles between different arriving troops
        if len(combatants) > 1:
            # Sort combatants by the number of cyborgs descending
            sorted_combatants = sorted(
                combatants.items(), key=lambda x: x[1], reverse=True
            )
            winner, winner_cyborgs = sorted_combatants[0]
            for loser, loser_cyborgs in sorted_combatants[1:]:
                winner_cyborgs -= loser_cyborgs  # Battle resolution
            combatants = {winner: max(0, winner_cyborgs)}  # Only the winner remains

        # Battle with factory defenders
        factory = self.factories[destination_factory]
        if factory.owner in combatants:
            # Reinforce if the factory's owner has arriving troops
            factory.cyborgs += combatants[factory.owner]
        else:
            # Determine the strongest attacking force
            attacking_force = max(combatants.values()) if combatants else 0
            if attacking_force > factory.cyborgs:
                # Factory is conquered
                new_owner = max(combatants, key=combatants.get)
                factory.owner = new_owner
                factory.cyborgs = attacking_force - factory.cyborgs
                factory.production = random.randint(
                    0, 3
                )  # Set new production rate for the conquering player
            else:
                factory.cyborgs -= attacking_force  # Defenders repel the attack

    def display_factories(self):
        for index, factory in enumerate(self.factories):
            owner = "Neutral"
            if factory.owner == 1:
                owner = "Player 1"
            elif factory.owner == 2:
                owner = "Player 2"
            print(f"Factory {index}: Owner = {owner}, Cyborgs = {factory.cyborgs}")


# Example usage
game = Game(10, 7)
# Assuming `game` is your game instance
visualizer = Visualizer(game)
game.send_troop(1, 5, 0, 2)  # Example command to send troops
game.update()  # Simulate a turn
game.send_bomb(1, 0, 6)
game.update()  # Simulate a turn
game.update()  # Simulate a turn
visualizer.visualize()
exit()
