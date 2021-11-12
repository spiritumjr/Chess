from tkinter import Tk, Canvas
from PIL import Image, ImageTk
from abc import ABC, abstractmethod

# In pixels
boardSize = 400
squareWIDTH = 50
boardWIDTH = squareWIDTH * 8


orthogonalDirections = [[0, 1], [1, 0], [0, -1], [-1, 0]]  # [Up, Right, Down, Left]
diagonalDirections = [[1, 1], [1, -1], [-1, -1], [-1, 1]]  # [Up-Right, Down-Right, Down-Left, Up Left]

TURN = 0


def main():

    # Initialisation of the GUI
    board = Tk()
    board.title("Chess")
    canvas = Canvas(board, width=boardSize, height=boardSize, highlightthickness=0)
    canvas.pack()

    # Converts coordinates in pixel position
    def convert_logical_to_grid_position(logical_position):
        return [logical_position[0] * squareWIDTH, logical_position[1] * squareWIDTH]

    # Converts pixel position in coordinates
    def convert_grid_to_logical_position(grid_position):
        return [grid_position[0] // squareWIDTH, grid_position[1] // squareWIDTH]

    # Opens and identifies the given image and makes it compatible with Tkinter (Receives a .png)
    def piece_images(img):
        piece_image = ImageTk.PhotoImage(Image.open(img).convert("RGBA"))
        return piece_image

    class Pieces(ABC):
        def __init__(self, logical_position, img, side: int):
            self.l_pos = logical_position  # Current coordinates of the piece
            self.image = img
            self.isSelected = False
            self.allies = None
            self.enemies = None
            self.is_white = side  # 0 if black, 1 if white
            self.first_move = True

        # Initializes self.allies, self.enemies and is_white
        def team(self):
            if self in pieces["w"]:
                self.allies = pieces["w"]
                self.enemies = pieces["b"]
                self.is_white = 1
            elif self in pieces["b"]:
                self.allies = pieces["b"]
                self.enemies = pieces["w"]
                self.is_white = 0

        # Places the selection image on a given position
        def draw_selection(self, grid_position):
            canvas.create_image(grid_position[0], grid_position[1], image=selectedImage, anchor="nw")
            for position in self.allowed_moves():
                logical_position = convert_logical_to_grid_position(position)
                canvas.create_image(logical_position[0], logical_position[1], image=allowedMoveImage, anchor="nw")

        # Places the piece's image on the GUI and calls draw_selection on a piece if it is selected
        def draw_piece(self):
            grid_position = convert_logical_to_grid_position(self.l_pos)
            canvas.create_image(grid_position[0], grid_position[1], image=self.image, anchor="nw")
            if self.isSelected:
                self.draw_selection(grid_position)

        # Removes a piece from its team (Removes it from the board)
        def obliteration(self):
            self.allies.remove(self)

        # This function is defined in the piece's subclass
        @abstractmethod
        def move_pattern(self):
            pass

        # Applies move pattern to a piece current position and removes the moves that are not in the board
        def piece_xray(self):
            move_pat_from_pos = [[[j[0] + self.l_pos[0], j[1] + self.l_pos[1]] for j in i] for i in self.move_pattern()]
            return [[b for b in a if 0 <= b[0] < 8 and 0 <= b[1] < 8]for a in move_pat_from_pos]

        # Same as piece_xray, but the directions stop at the first on the first enemy
        def directions_xray(self):
            pmd = []
            for i in self.piece_xray():
                direction = []
                for j in i:
                    if j in [x.l_pos for x in self.allies]:
                        break
                    else:
                        direction.append(j)
                        if j in [x.l_pos for x in self.enemies]:
                            break
                pmd.append(direction)
            return pmd

        # Stops the directions before the first ally and on the
        def possible_moves(self):
            realistic_moves = []

            for i in self.piece_xray():
                for j in i:
                    if j in [x.l_pos for x in self.allies]:
                        break
                    else:
                        realistic_moves.append(j)
                        if j in [x.l_pos for x in self.enemies]:
                            break
            return realistic_moves

        def possible_takes(self):
            nff = []
            for i in self.piece_xray():
                direction = []
                for j in i:
                    if j in [x.l_pos for x in self.allies]:
                        break
                    else:
                        direction.append(j)
                nff.append(direction)
            targets = [[k for j in i for k in self.enemies if k.l_pos == j] for i in nff]
            return targets

        def targeted_pieces(self):
            targets = [[k for j in i for k in self.enemies if k.l_pos == j] for i in self.possible_takes()]
            return targets

        def defended_squares(self):
            defended_pieces = []

            for i in self.piece_xray():
                for j in i:
                    if j in [x.l_pos for x in self.enemies if not isinstance(x, King)]:
                        break
                    else:
                        defended_pieces.append(j)
                        if j in [x.l_pos for x in self.allies]:
                            break
            return defended_pieces

        def is_pinned(self):
            for i in self.enemies:
                for j in i.possible_takes():
                    is_blocker = 0
                    pos = 0
                    for k in j:
                        if isinstance(k, King) and pos == 1 and is_blocker:
                            return [i.l_pos] + [y for x in i.piece_xray() for y in x if self.l_pos in x]

                        if k == self and pos == 0:
                            is_blocker = 1
                        pos += 1
            return []

        def allowed_moves(self):
            if self.is_pinned():
                return [i for i in self.possible_moves() if i in self.is_pinned()]
            for i in self.allies:
                if isinstance(i, King) and i.is_checked():
                    return [j for j in self.possible_moves() if j in i.is_checked()]
            return self.possible_moves()

    class Rook(Pieces):
        def __init__(self, logical_position, img, side):
            super().__init__(logical_position, img, side)

        def move_pattern(self):
            return [[[i[0] * j, i[1] * j] for j in range(1, 8)] for i in orthogonalDirections]

    class Knight(Pieces):
        def __init__(self, logical_position, img, side):
            super().__init__(logical_position, img, side)

        def move_pattern(self):
            return [[[i[0] * (j + 1), i[1] * (0 ** j + 1)]] for i in diagonalDirections for j in range(2)]

    class Bishop(Pieces):
        def __init__(self, logical_position, img, side):
            super().__init__(logical_position, img, side)

        def move_pattern(self):
            return [[[i[0] * j, i[1] * j] for j in range(1, 8)] for i in diagonalDirections]

    class Queen(Pieces):
        def __init__(self, logical_position, img, side):
            super().__init__(logical_position, img, side)

        def move_pattern(self):
            return [[[i[0] * j, i[1] * j] for j in range(1, 8)] for i in orthogonalDirections + diagonalDirections]

    class King(Pieces):
        def __init__(self, logical_position, img, side):
            super().__init__(logical_position, img, side)

        def can_castle(self):
            objections = []
            castle_available = []
            if self.first_move:
                for i in self.allies:
                    if isinstance(i, Rook) and i.first_move:
                        if self.l_pos in i.defended_squares():
                            if not self.is_checked():
                                for j in self.enemies:
                                    for k in j.possible_moves():
                                        if k in i.defended_squares():
                                            objections.append(k)
                                if not objections:
                                    if i.l_pos[0] == 0:
                                        castle_available.append([2, self.l_pos[1]])
                                    else:
                                        castle_available.append([6, self.l_pos[1]])
            return castle_available

        def is_checked(self):
            for i in self.enemies:
                for j in i.directions_xray():
                    if self.l_pos in j:
                        attack = j
                        attack.append(i.l_pos)
                        return attack
            return False

        def is_checkmated(self):
            interceptor = []
            if self.is_checked():
                if not self.allowed_moves():
                    for i in self.enemies:
                        for j in i.directions_xray():
                            if self.l_pos in j:
                                for k in self.allies:
                                    if isinstance(k, King):
                                        continue
                                    for m in k.allowed_moves():
                                        if m in j or m == i.l_pos:
                                            interceptor.append(m)
                    if interceptor:
                        return False
                    else:
                        return True
            else:
                return False

        def move_pattern(self):
            return [[i] for i in orthogonalDirections + diagonalDirections]

        def allowed_moves(self):
            a_m = [i for i in self.possible_moves() if i not in [k for j in self.enemies for k in j.defended_squares()]]
            return a_m + self.can_castle()

    class Pawn(Pieces):
        def __init__(self, logical_position, img, side):
            super().__init__(logical_position, img, side)
            self.attack_pattern = [[-1, 1], [1, 1]]
            self.is_vulnerable = False
            self.passant = None

        def directions_xray(self):
            return self.defended_squares()

        def promotes(self):
            if self.l_pos[1] == 0 or self.l_pos[1] == 7:
                if self.is_white:
                    return whiteQueenImage
                else:
                    return blackQueenImage
            return False

        def defended_squares(self):
            return self.possible_attack()

        def possible_moves_directions(self):
            return [[i] for i in self.defended_squares()]

        def move_pattern(self):
            if self.first_move:
                pattern = [[[0, 1], [0, 2]]]
            else:
                pattern = [[[0, 1]]]

            if self in pieces["w"]:
                return [[[i[0], i[1] * -1]for i in pattern[0]]]
            else:
                return pattern

        def possible_attack(self):
            if self in pieces["w"]:
                return [[i[0] + self.l_pos[0], i[1] * -1 + self.l_pos[1]] for i in self.attack_pattern]
            else:
                return [[i[0] + self.l_pos[0], i[1] + self.l_pos[1]] for i in self.attack_pattern]

        def vul_p(self):
            return [i for i in self.enemies if isinstance(i, Pawn) if i.is_vulnerable]

        def allowed_moves(self):
            allowed_moves = []
            vul_p = self.vul_p()
            p_a = self.possible_attack()
            for i in self.piece_xray():
                for j in i:
                    if j in [x.l_pos for x in pieces[relation("ally")]]:
                        break
                    elif j in [x.l_pos for x in pieces[relation("enemy")]]:
                        break
                    else:
                        allowed_moves.append(j)

            attack_moves = [i for i in self.possible_attack() if i in [i.l_pos for i in self.enemies]]
            passant = [i for i in p_a if i in [[i.l_pos[0], i.l_pos[1] + self.move_pattern()[0][0][1]] for i in vul_p]]
            self.passant = passant
            allowed_moves += attack_moves + passant
            if self.is_pinned():
                return [i for i in allowed_moves if i in self.is_pinned()]
            for i in self.allies:
                if isinstance(i, King) and i.is_checked():
                    return [j for j in allowed_moves if j in i.is_checked()]
            return allowed_moves

    blackPawnImage = piece_images("BlackPawn.png")
    whitePawnImage = piece_images("WhitePawn.png")
    blackRookImage = piece_images("BlackRook.png")
    whiteRookImage = piece_images("WhiteRook.png")
    blackKnightImage = piece_images("BlackKnight.png")
    whiteKnightImage = piece_images("WhiteKnight.png")
    blackBishopImage = piece_images("BlackBishop.png")
    whiteBishopImage = piece_images("WhiteBishop.png")
    blackQueenImage = piece_images("BlackQueen.png")
    whiteQueenImage = piece_images("WhiteQueen.png")
    blackKingImage = piece_images("BlackKing.png")
    whiteKingImage = piece_images("WhiteKing.png")

    checkedBlackKingImage = piece_images("CheckedBlackKing.png")
    checkedWhiteKingImage = piece_images("CheckedWhiteKing.png")
    checkMatedBlackKingImage = piece_images("CheckmatedBlackKing.png")
    checkMatedWhiteKingImage = piece_images("CheckmatedWhiteKing.png")

    selectedImage = piece_images("Selected.png")
    allowedMoveImage = piece_images("AllowedMove.png")

    pieces = {"w": [], "b": []}

    pieces["w"] += [Pawn([i, 6], whitePawnImage, 1) for i in range(8)]
    pieces["w"] += [Rook([i, 7], whiteRookImage, 1) for i in (0, 7)]
    pieces["w"] += [Knight([i, 7], whiteKnightImage, 1) for i in (1, 6)]
    pieces["w"] += [Bishop([i, 7], whiteBishopImage, 1) for i in (2, 5)]
    pieces["w"] += [Queen([3, 7], whiteQueenImage, 1)]
    pieces["w"] += [King([4, 7], whiteKingImage, 1)]

    pieces["b"] += [Pawn([i, 1], blackPawnImage, 0) for i in range(8)]
    pieces["b"] += [Rook([i, 0], blackRookImage, 0) for i in (0, 7)]
    pieces["b"] += [Knight([i, 0], blackKnightImage, 0) for i in (1, 6)]
    pieces["b"] += [Bishop([i, 0], blackBishopImage, 0) for i in (2, 5)]
    pieces["b"] += [Queen([3, 0], blackQueenImage, 0)]
    pieces["b"] += [King([4, 0], blackKingImage, 0)]

    for team in ["w", "b"]:
        for item in pieces[team]:
            item.team()

    def team_playing():
        if TURN % 2 == 0:
            return ["w", "b"]
        else:
            return ["b", "w"]

    def relation(ally_or_enemy):
        if ally_or_enemy == "ally":
            return team_playing()[0]
        elif ally_or_enemy == "enemy":
            return team_playing()[1]

    def draw_pieces():
        for whitePiece in pieces["w"]:
            whitePiece.draw_piece()

        for blackPiece in pieces["b"]:
            blackPiece.draw_piece()

    def draw_board():
        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 0:
                    color = "slate gray"
                else:
                    color = "dark slate gray"
                x1 = squareWIDTH * j
                y1 = squareWIDTH * i
                x2 = x1 + squareWIDTH
                y2 = y1 + squareWIDTH
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def actualize_board():
        canvas.delete("all")
        draw_board()
        draw_pieces()

    def king_status():
        for i in pieces[relation("ally")]:
            if isinstance(i, King):
                if i.is_white:
                    if i.is_checkmated():
                        i.image = checkMatedWhiteKingImage
                    elif i.is_checked():
                        i.image = checkedWhiteKingImage
                    else:
                        i.image = whiteKingImage
                else:
                    if i.is_checkmated():
                        i.image = checkMatedBlackKingImage
                    elif i.is_checked():
                        i.image = checkedBlackKingImage
                    else:
                        i.image = blackKingImage

    draw_board()
    draw_pieces()

    def click(event):
        grid_position = [event.x, event.y]
        logical_position = convert_grid_to_logical_position(grid_position)
        selectedPiece = [piece for piece in pieces[relation("ally")] if piece.isSelected]
        if selectedPiece:
            el_piece = selectedPiece[0]
            for move in el_piece.allowed_moves():
                if move == logical_position:
                    el_piece.l_pos = move
                    if isinstance(el_piece, King) and el_piece.can_castle():
                        if logical_position[0] == 2:
                            for i in el_piece.allies:
                                if i.l_pos[0] == 0 and isinstance(i, Rook):
                                    i.l_pos = [3, i.l_pos[1]]
                                    i.first_move = False
                        elif logical_position[0] == 6:
                            for i in el_piece.allies:
                                if i.l_pos[0] == 7 and isinstance(i, Rook):
                                    i.l_pos = [5, i.l_pos[1]]
                                    i.first_move = False

                    if el_piece.first_move:
                        el_piece.first_move = False
                        if isinstance(el_piece, Pawn) and el_piece.l_pos[1] == 3 or 4:
                            el_piece.is_vulnerable = True
                    if isinstance(el_piece, Pawn):
                        direct = el_piece.move_pattern()[0][0][1]
                        for vul in el_piece.enemies:
                            if vul.l_pos == [el_piece.l_pos[0], el_piece.l_pos[1] - direct]:
                                vul.obliteration()

                    for piece in el_piece.enemies:
                        if piece.l_pos == move:
                            piece.obliteration()

                    if isinstance(el_piece, Pawn) and el_piece.promotes():
                        el_piece.allies[el_piece.allies.index(el_piece)] = Queen(el_piece.l_pos, el_piece.promotes(), el_piece.is_white)
                        for i in ["w", "b"]:
                            for j in pieces[i]:
                                j.team()

                    king_status()
                    global TURN
                    TURN += 1

            el_piece.isSelected = False
        else:

            for piece in pieces[relation("ally")]:
                if piece.l_pos == logical_position:
                    piece.isSelected = True
                if isinstance(piece, Pawn) and piece.is_vulnerable:
                    piece.is_vulnerable = False

        king_status()
        actualize_board()

    board.bind("<Button-1>", click)

    board.mainloop()


if __name__ == '__main__':
    main()
