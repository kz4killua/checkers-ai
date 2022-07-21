import random
import copy
import pygame
import time
import cProfile

# Initialize the pygame module.
pygame.init()

FPS = 10
ROWS = 8
COLS = 8
SQUARE_WIDTH = 50
SCREEN_WIDTH = SQUARE_WIDTH * COLS
SCREEN_HEIGHT = SQUARE_WIDTH * ROWS
LIGHT_SQUARE_COLOUR = (240,220,130)
DARK_SQUARE_COLOUR = (0,128,0)
WHITE_PIECE_COLOUR = (255,255,255)
BLACK_PIECE_COLOUR = (255,0,0)
HIGHLIGHT_COLOUR = (173, 255, 47)
VALID_MOVE_HIGHLIGHT_RADIUS = 10
PIECE_RADIUS = 20
PIECES_PER_SIDE = 12
CROWN = pygame.transform.scale(pygame.image.load('images\\crown.png'), (25, 25))
CLICK_SOUND = pygame.mixer.Sound('sounds\\click.wav')
CROWN_SOUND = pygame.mixer.Sound('sounds\\crown.wav')
WIN_SOUND = pygame.mixer.Sound('sounds\\win.wav')


class Piece:

    def __init__(self, colour, position, crowned=False):
        self.colour = colour
        self.position = position
        self.crowned = crowned

    def draw(self):
        pygame.draw.circle(screen, self.colour, 
        (self.position[0] * SQUARE_WIDTH + (SQUARE_WIDTH // 2), 
        self.position[1] * SQUARE_WIDTH + (SQUARE_WIDTH // 2)), PIECE_RADIUS)

        # Draw crowns for crowned pieces.
        if self.crowned == True:
            screen.blit(CROWN, 
            (self.position[0] * SQUARE_WIDTH + (SQUARE_WIDTH // 2) - CROWN.get_width()//2, 
            self.position[1] * SQUARE_WIDTH + (SQUARE_WIDTH // 2) - CROWN.get_width()//2))


class Board:

    def __init__(self):
        
        self.pieces = []

        # Prepare White's pieces.
        self.pieces += [Piece(WHITE_PIECE_COLOUR, [left, top]) for top 
                        in range(ROWS-1, (ROWS-1)-(PIECES_PER_SIDE//(COLS//2)), -1) 
                        for left in range((top + 1) % 2 , COLS, 2)]
        # Prepare Black's pieces.
        self.pieces += [Piece(BLACK_PIECE_COLOUR, [left, top]) for top 
                        in range(0, (PIECES_PER_SIDE//(COLS//2)), 1) 
                        for left in range((top + 1) % 2 , COLS, 2)]

        self.no_of_white = PIECES_PER_SIDE
        self.no_of_black = PIECES_PER_SIDE

        self.turn = WHITE_PIECE_COLOUR
        self.active_piece = None
        self.active_piece_valid_moves = []

        # Create a list to hold the pieces captured in that turn
        self.captured_pieces = []

    def draw(self):

        # First, draw a huge square in one colour.
        pygame.draw.rect(screen, DARK_SQUARE_COLOUR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Then draw the other squares to complete the checkered board.
        for top in range(ROWS):       
            for left in range(top % 2, COLS, 2):
                pygame.draw.rect(screen, LIGHT_SQUARE_COLOUR,
                    (left * SQUARE_WIDTH, top * SQUARE_WIDTH, SQUARE_WIDTH, SQUARE_WIDTH))

        # Highlight the square the active piece is on (if any).
        if self.active_piece != None:
            pygame.draw.rect(screen, HIGHLIGHT_COLOUR, 
            (self.active_piece.position[0] * SQUARE_WIDTH, 
            self.active_piece.position[1] * SQUARE_WIDTH,
            SQUARE_WIDTH, SQUARE_WIDTH))

        # Next, draw the pieces.
        for piece in self.pieces:
            piece.draw()

        # If there is an active piece, draw its valid moves.
        for move in self.active_piece_valid_moves:
            pygame.draw.circle(screen, HIGHLIGHT_COLOUR, 
            (move[0] * SQUARE_WIDTH + (SQUARE_WIDTH // 2), 
            move[1] * SQUARE_WIDTH + (SQUARE_WIDTH // 2)),
            VALID_MOVE_HIGHLIGHT_RADIUS)

        # Draw captured pieces
        for piece in self.captured_pieces:
            piece.draw()

    def check_piece_at(self, position):
        
        # Check if any piece is in that position.
        for piece in self.pieces:
            if piece.position == position:
                return piece
        # Else, return 'None'
        else:
            return None

    def set_active(self, piece):

        self.active_piece = piece
        # Check the possible moves the active piece can make.
        self.active_piece_valid_moves = self.get_valid_moves(piece)

    def get_valid_moves(self, piece):

        valid_moves = []

        if piece.crowned == False:

            # These are the two simple moves an uncrowned piece can make.
            if piece.colour == WHITE_PIECE_COLOUR:
                options = [[1, -1], [-1, -1]]
            else:
                options = [[1, 1], [-1, 1]]

        else:

            # These are the four simple moves a crowned piece can make.
            options = [[1, -1], [-1, -1], [1, 1], [-1, 1]]

        # First check for any possible captures.
        for option in options:

            simple_move = [piece.position[0] + option[0], piece.position[1] + option[1]]
            jump = [piece.position[0] + option[0] * 2, piece.position[1] + option[1] * 2]
            piece_at_simple_move = self.check_piece_at(simple_move)
            piece_at_jump = self.check_piece_at(jump)

            # If there is a piece diagonally opposite
            if (type(piece_at_simple_move) == Piece
            # and the piece is an opponent piece
            and piece_at_simple_move.colour != piece.colour
            # and the jump destination is valid
            and 0 <= jump[0] <= 7
            and 0 <= jump[1] <= 7
            # and there is no piece at the jump destination
            and piece_at_jump == None):

                # the capture is valid.
                valid_moves.append(jump)

        # Now check for simple moves (if no jumps are possible).
        if valid_moves == []:
            
            for option in options:

                simple_move = [piece.position[0] + option[0], piece.position[1] + option[1]]
                piece_at_simple_move = self.check_piece_at(simple_move)

                # If the move is in the board
                if (0 <= simple_move[0] <= 7 
                and 0 <= simple_move[1] <= 7
                # and there is no piece at the destination.
                and piece_at_simple_move == None):

                    # the move is valid.
                    valid_moves.append(simple_move)

        return valid_moves

    def make_move(self, piece, new_position):
        
        # Check if the move is a capture.
        if abs(new_position[0] - piece.position[0]) == 2:
            capture = True
        else:
            capture = False

        # If the move is a capture...
        if capture == True:
            # ...check the piece to capture.
            mid = [(new_position[0] + piece.position[0]) // 2,
            (new_position[1] + piece.position[1]) // 2]
            piece_to_capture = self.check_piece_at(mid)
            # Capture the piece.
            self.capture_piece(piece_to_capture)

        # Move the piece to the new position.
        piece.position = new_position

    def capture_piece(self, piece):
        
        # Add the piece to the list of captured pieces.
        self.captured_pieces.append(piece)
        # Update the number of pieces.
        if piece.colour == WHITE_PIECE_COLOUR:
            self.no_of_white -= 1
        else:
            self.no_of_black -= 1
        # Remove the piece from the list of pieces.
        self.pieces.remove(piece)

    def end_turn(self):

        # Check for crowning.
        if (self.active_piece.colour == WHITE_PIECE_COLOUR 
        and self.active_piece.position[1] == 0
        and self.active_piece.crowned == False):
            self.crown_piece(self.active_piece)
        elif (self.active_piece.colour == BLACK_PIECE_COLOUR 
        and self.active_piece.position[1] == 7
        and self.active_piece.crowned == False):
            self.crown_piece(self.active_piece)
        
        # Reset the captured pieces.
        self.captured_pieces.clear()

        # Switch turns.
        if self.turn == WHITE_PIECE_COLOUR:
            self.turn = BLACK_PIECE_COLOUR
        else:
            self.turn = WHITE_PIECE_COLOUR
        
        # Reset the active piece.
        self.active_piece = None
        # Reset the valid moves.
        self.active_piece_valid_moves.clear()

    def crown_piece(self, piece):

        # Crown the piece.
        piece.crowned = True

    def is_won(self):
        # If it is Black's turn and Black has no pieces left...
        if self.turn == BLACK_PIECE_COLOUR and self.no_of_black == 0:
            return True
        # If it is White's turn and White has no pieces left...
        elif self.turn == WHITE_PIECE_COLOUR and self.no_of_white == 0:
            return True
        else:
            for piece in self.pieces:
                if piece.colour == self.turn and self.get_valid_moves(piece) != []:
                    break
            # If the player has no pieces that can move..
            else:
                return True


class AI:

    def __init__(self, board, colour, difficulty):
        self.board = board
        self.colour = colour
        self.difficulty = difficulty

    def get_static_value(self, board_state, depth):
        
        static_value = 0

        if board_state.is_won():
            # If the AI wins...
            if board_state.turn != self.colour:
                static_value += 20
            # If the AI loses...
            else:
                static_value -= 20
            
        for piece in board_state.pieces:

            if piece.colour == self.colour:
                if piece.crowned == False:
                    # +1 for each uncrowned friendly  piece
                    static_value += 1
                else:
                    # +2 for each crowned friendly piece
                    static_value += 2
            
            else:
                if piece.crowned == False:
                    # -1 for each uncrowned opponent piece
                    static_value -= 1
                else:
                    # -2 for each crowned opponent piece
                    static_value -= 2 
                
        # Take the depth into account. We would like to win as quickly as possible.
        static_value -= depth

        return static_value

    def get_future_piece_states(self, board_state, piece):

        future_piece_states = []

        # Get all the positions the piece can move to.
        valid_moves = board_state.get_valid_moves(piece)

        for position in valid_moves:

            # Make a copy of the board and the piece.
            copy_board_state = copy.deepcopy(board_state)
            copy_piece = copy.deepcopy(piece)

            # Set the piece as active.
            copy_board_state.set_active(copy_piece)

            # Make each move. Captures are done within the method.
            copy_board_state.make_move(copy_piece, position)

            # Check the piece's next moves.
            next_valid_moves = copy_board_state.get_valid_moves(copy_piece)

            # If a multi-jump is possible.
            if (copy_board_state.captured_pieces != []
            and next_valid_moves != []
            and abs(next_valid_moves[0][0] - copy_board_state.active_piece.position[0]) == 2):

                # Call recursively.
                more_states = self.get_future_piece_states(copy_board_state, copy_piece)
                # Add the new states to the list.
                future_piece_states.extend(more_states)

            else:
                # End turn.
                copy_board_state.end_turn()
                # Put the piece into the board.
                copy_board_state.pieces.append(copy_piece)
                # Save the board state to the list.
                future_piece_states.append(copy_board_state)

        return future_piece_states

    def get_future_board_states(self, board_state):

        future_board_states = []

        for piece in board_state.pieces:

            if piece.colour == board_state.turn:

                # Check the piece's valid moves.
                valid_moves = board_state.get_valid_moves(piece)

                # If the piece cannot move, skip.
                if len(valid_moves) == 0:
                    continue

                # If the piece can capture,
                elif abs(valid_moves[0][0] - piece.position[0]) == 2:
                    # Store the piece index.
                    index = board_state.pieces.index(piece)
                    # Separate the piece from the board.
                    board_state.pieces.remove(piece)
                    # Get future states.
                    future_board_states.extend(self.get_future_piece_states(board_state, piece))
                    # Put the piece back into the board.
                    board_state.pieces.insert(index, piece)

                else:

                    for other_piece in board_state.pieces:
                        other_piece_valid_moves = board_state.get_valid_moves(other_piece)
                        # Check if any other piece can capture.
                        if (other_piece.colour == board_state.turn
                        and other_piece_valid_moves != [] 
                        and abs(other_piece_valid_moves[0][0] - other_piece.position[0]) == 2):
                            break

                    # If no other piece can capture, then the piece can move.
                    else:
                        # Store the piece index.
                        index = board_state.pieces.index(piece)
                        # Separate the piece from the board.
                        board_state.pieces.remove(piece)
                        # Get future states.
                        future_board_states.extend(self.get_future_piece_states(board_state, piece))
                        # Put the piece back into the board.
                        board_state.pieces.insert(index, piece)

        return future_board_states

    def get_best_move(self, board_state, alpha, beta, depth, depth_limit, is_maximizer):
    
        if depth == depth_limit or board_state.is_won():
            return (board_state, self.get_static_value(board_state, depth))
    
        # Get all possible future states.
        future_states = self.get_future_board_states(board_state)
    
        # Shuffle the future states.
        random.shuffle(future_states)
    
        if is_maximizer:
        
            evaluated_states = []
    
            for state in future_states:
                # Call recursively to get the static value of that branch.
                evaluated_state = self.get_best_move(state, alpha, beta, depth + 1, depth_limit, False)
                evaluated_states.append((state, evaluated_state[1]))
                # Compare with alpha.
                if evaluated_state[1] > alpha:
                    alpha = evaluated_state[1]
                # Check for pruning.
                if beta <= min(evaluated_states, key=lambda evaluated_state: evaluated_state[1])[1]:
                    break
                
            # Return the largest (max) option.
            return max(evaluated_states, key=lambda evaluated_states: evaluated_states[1])
    
        else:
        
            evaluated_states = []
    
            for state in future_states:
                # Call recursively to get the static value of that branch.
                evaluated_state = self.get_best_move(state, alpha, beta, depth + 1, depth_limit, True)
                evaluated_states.append((state, evaluated_state[1]))
                # Compare with beta.
                if evaluated_state[1] < beta:
                    beta = evaluated_state[1]
                # Check for pruning.
                if alpha >= max(evaluated_states, key=lambda evaluated_state: evaluated_state[1])[1]:
                    break
                
            # Return the smallest (min) option.
            return min(evaluated_states, key=lambda evaluated_states: evaluated_states[1])
    
    def play(self):
        self.board = self.get_best_move(self.board, float('-inf'), float('+inf'), 0, self.difficulty, True)[0]
        return self.board


def refresh_display():

    screen.fill((0,0,0))
    b.draw()
    pygame.display.update()


def main():

    global b

    refresh_display()

    running = True
    while running:

        # Limit the framerate.
        clock.tick(FPS)

        if b.turn == ai.colour:
            b = ai.play()
            refresh_display()
            continue

        for event in pygame.event.get():

            # Did the user click on the 'quit' button?
            if event.type == pygame.QUIT:
                running = False

            # Did the user click the mouse?
            elif event.type == pygame.MOUSEBUTTONUP:
                
                # Save the position of the mouse.
                mouse_position = pygame.mouse.get_pos()

                # Convert the mouse position to columns and rows.
                col_row = [mouse_position[0] // SQUARE_WIDTH, 
                mouse_position[1] // SQUARE_WIDTH]

                # Check what the user clicked on.
                clicked = b.check_piece_at(col_row)

                # If the user clicked on a piece
                if (type(clicked) == Piece
                # and it's that colour's turn to play
                and clicked.colour == b.turn 
                # and a move is not in progress
                and b.captured_pieces == []):

                    # Check its valid moves
                    valid_moves = b.get_valid_moves(clicked)

                    # If the piece has no valid moves, skip
                    if valid_moves == []:
                        pass

                    # If the piece can capture...
                    elif abs(valid_moves[0][0] - clicked.position[0]) == 2:
                        # ...set that piece as active.
                        b.set_active(clicked)

                    # If the piece cannot capture, check if any other piece can
                    else:

                        for piece in b.pieces:
                            # If it is that colour's turn,
                            if piece.colour == b.turn:
                                # check all its valid moves
                                piece_moves = b.get_valid_moves(piece)
                                # If the piece can move and capture
                                if (piece_moves != []
                                and abs(piece_moves[0][0] - piece.position[0]) == 2):
                                    break

                        # If no other piece can capture
                        else:
                            # set it as active
                            b.set_active(clicked)
                                              

                # If the user clicks on a position and it's a valid position...
                elif col_row in b.active_piece_valid_moves:

                    # ...move the active piece to that position 
                    # (make captures if possible)
                    b.make_move(b.active_piece, col_row)
                    # Play sound.
                    CLICK_SOUND.play()
                    
                    next_moves = b.get_valid_moves(b.active_piece)
                    # If a piece has been captured....
                    if (b.captured_pieces != []
                    # but the active piece can still move...
                    and next_moves != []
                    # and capture...
                    and abs(next_moves[0][0] - b.active_piece.position[0]) == 2):
                        # Reset the valid moves but do not end turn
                        b.active_piece_valid_moves = next_moves

                    else:
                        # End the turn
                        b.end_turn()
                        # Check if the game is won.
                        if b.is_won():
                            refresh_display()
                            WIN_SOUND.play()
                            clock.tick(1)
                            running = False

                # Refresh the display after each click.
                refresh_display()


# Create a new board object.
b = Board()
# Create the AI
ai = AI(b, BLACK_PIECE_COLOUR, 2)
# Create the screen.
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# Set a window caption.
pygame.display.set_caption('English Draughts!')
# Add an icon.
pygame.display.set_icon(pygame.image.load('images\\icon.png'))

# Create a 'Clock' object
clock = pygame.time.Clock()


main()