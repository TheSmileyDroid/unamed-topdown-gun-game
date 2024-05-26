import pickle

import pygame


def serialize_state(player):
    """Serialize the player's state."""
    return {
        "uuid": player.uuid,
        "position": (player.x, player.y),
        "rotation": player.rotation,
        "hp": player.hp,
        "score": player.score,
        "is_shooting": player.is_shooting(),
        "motion": player.motion,
        "crosshair": player.crosshair.pos,
    }


def deserialize_state(state, player):
    """Deserialize the player's state."""
    player.x, player.y = state["position"]
    player.rotation = state["rotation"]
    player.hp = state["hp"]
    player.score = state["score"]
    player._is_shooting = state["is_shooting"]
    player.motion = pygame.Vector2(state["motion"].x, state["motion"].y)
    player.crosshair.pos = state["crosshair"]


def send_state(player, connection):
    """Send the player's state to the connection."""
    try:
        state = serialize_state(player)
        connection.sendall(pickle.dumps(state))
    except BrokenPipeError:
        exit(1)
    except Exception as e:
        print(f"Failed to send update: {e}")


def receive_state(connection, player):
    """Receive the player's state from the connection
    and update the player's state."""
    try:
        data = connection.recv(1024)
        if data:
            state = pickle.loads(data)
            deserialize_state(state, player)
    except Exception as e:
        print(f"Failed to receive update: {e}")


def broadcast_state(players):
    """Broadcast the players state to all players."""
    try:
        state = {}
        for player in players:
            state[player.uuid] = serialize_state(player)

        for player in players:
            if hasattr(player, "connection"):
                try:
                    player.connection.send(pickle.dumps(state))
                except BrokenPipeError:
                    del player.connection
                    players.remove(player)
    except Exception as e:
        print(f"Failed to broadcast update: {e}")


def receive_broadcast(connection):
    """Receive the players state from the connection."""
    try:
        data = connection.recv(1024)
        if data:
            state = pickle.loads(data)
            return state
    except BrokenPipeError:
        exit(1)
    except Exception as e:
        print(f"Failed to receive broadcast: {e}")
        return None


def send_initial_info(connection, uuid):
    """Send the initial info to the connection."""
    try:
        connection.sendall(pickle.dumps({"uuid": uuid}))
    except Exception as e:
        print(f"Failed to send initial info: {e}")


def receive_initial_info(connection):
    """Receive the initial info from the connection."""
    try:
        data = connection.recv(1024)
        if data:
            info = pickle.loads(data)
            return info
    except BrokenPipeError:
        exit(1)
    except Exception as e:
        print(f"Failed to receive initial info: {e}")
        return None
