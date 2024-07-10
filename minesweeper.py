import os
import tkinter as tk
from tkinter import font as tkFont
from tkinter import messagebox
import random
from threading import *
import time
import mysql.connector


class Minesweeper(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MINESWEEPER")
        self.difficulty = [[9,10,"300x300"], [16,40,"450x450"], [24,99,"650x650"]]
        self.geometry("300x300")
        self.size = self.difficulty[0][0]
        self.minesLeft = self.mines = self.difficulty[0][1]
        self.gameOverFlag = False
        self.thread = self.totaltime = 0
        self.firstMoveFlag = True
        self.dbConnectionFlag = False
        self.lvl = "SMALL"
        self.colors = ["black","blue","green","red","navy","maroon"]
        self.getName()
        

    def clearWindow(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        for widget in self.widgets.winfo_children():
            widget.destroy()
        self.widgets.destroy()
        self.menu.destroy()

    def readFromDB(self, lvl):
        sql = "SELECT name, time FROM tabela where level=\"" + lvl + "\" order by time"
        self.dbcursor.execute(sql)
        return self.dbcursor.fetchall()

    def showScores(self, i):
        if not self.dbConnectionFlag:
            return
        lvl = "SMALL" if i==0 else "MEDIUM" if i==1 else "LARGE"

        self.clearWindow()
        data = self.readFromDB(lvl)

        formatedData = "LEVEL " + lvl + "\n"
        for name, time in data:
            formatedData += name.replace("\n","") + " " + str(time) + "\n"

        tk.Label(self.frame,text=formatedData).pack(fill="both")
        tk.Button(self.frame, text="Go Back", command=self.goBack).pack(fill="both")

        
    def goBack(self):
        self.setup_board()

    def getName(self):
        self.frame = tk.Frame(self)
        self.frame.pack()
        tk.Label(self.frame, pady=20).pack()
        tk.Label(self.frame,text="Type your name:", pady=10).pack()
        fMenuTextBox = tk.Text(self.frame, width=30, height=1)
        fMenuTextBox.pack()
        tk.Label(self.frame, pady=5).pack()
        self.fMenuSubmitBtn = tk.Button(self.frame, width=10, pady=8, height=1, text="SUBMIT")
        self.fMenuSubmitBtn.pack()
        self.fMenuSubmitBtn.bind("<Button-1>", lambda e: self.saveText(fMenuTextBox))

    def saveText(self, text):
        self.name = text.get(1.0,tk.END)
        self.name.replace("\n","")
        self.setup_board()
    
    def setup_board(self):
        self.setup_menu()
        self.create_widgets()
        self.reset_game()

    def saveScore(self):
        if self.dbConnectionFlag:
            sql = "INSERT INTO tabela (name, level, time) VALUES(%s,%s,%s)"
            val = (str(self.name), self.lvl, self.totaltime)
            self.dbcursor.execute(sql, val)
            self.mydb.commit()
        return

    # ŁĄCZENIE DO BAZY DANYCH
    def connectToDB(self):
        self.mydb = mysql.connector.connect(
            host="localhost",
            user = "root",
            password = "",
        )

    def checkDB(self):
        try:
            self.connectToDB()
        except:
            print("Can't connect to local DB")
        else:
            print("OK - connected to local server")
            self.dbcursor = self.mydb.cursor()
            try:
                self.dbcursor.execute("USE saper")
            except:
                try:
                    self.dbcursor.execute("CREATE DATABASE saper")
                    self.dbcursor.execute("USE saper")
                except:
                    print("Can't create a database")
                else:
                    print("OK - created and connected to DB")
            else:
                print("OK - connected to DB")
                self.dbcursor.execute("SHOW TABLES")
                for x in self.dbcursor:
                    if "tabela" in x:
                        print("OK - Table exist")
                        self.dbConnectionFlag = True
                        self.db.config(foreground="green")
                        return
                else:
                    try:
                        self.dbcursor.execute("CREATE TABLE tabela (name VARCHAR(100), level VARCHAR(20), time float)")
                    except:
                        print("Table don't exist and can't create fresh one")
                    else:
                        print("OK - created table")
                        self.dbConnectionFlag = True
                        self.db.config(foreground="green")
                        return
        self.dbConnectionFlag = False
        self.db.config(foreground="red")

    # LICZENIE CZASU
    def start_timer(self):
        self.gameOverFlag = False
        self.thread = Thread(target=self.timer, daemon=True)
        self.thread.start()

    def timer(self):
        self.totaltime = 0
        self.starttime = time.time()
        while True:
           time.sleep(0.01)
           self.totaltime = round((time.time() - self.starttime), 2)
           self.tVar.set(self.totaltime)
           if self.gameOverFlag:
               break
        
    # USTAWIENIE MENU
    def setup_menu(self):
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        self.game_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Game", menu=self.game_menu)
        self.game_menu.add_command(label="New Game", command=self.reset_game)
        self.game_menu.add_separator()
        self.game_menu.add_command(label="Exit", command=self.quit)

        options_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Options", menu=options_menu)

        options_menu.add_command(label="Small (9x9, 10 mines)", command=lambda: self.set_difficulty(0))
        options_menu.add_command(label="Medium (16x16, 40 mines)", command=lambda: self.set_difficulty(1))
        options_menu.add_command(label="Large (24x24, 99 mines)", command=lambda: self.set_difficulty(2))

        self.menu.add_command(label="Reset", command=self.reset_game)

        self.db = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="DataBase", menu=self.db)
        self.db.add_command(label="Connect", command=self.checkDB)
        self.db.config(foreground="green") if self.dbConnectionFlag else self.db.config(foreground="red")

        self.scores = tk.Menu(self.menu, tearoff = 0)
        self.menu.add_cascade(label="Scores", menu=self.scores)
        self.scores.add_command(label="SMALL", command=lambda: self.showScores(0))
        self.scores.add_command(label="MEDIUM", command=lambda: self.showScores(1))
        self.scores.add_command(label="LARGE", command=lambda: self.showScores(2))

    def set_difficulty(self, i):
        self.size = self.difficulty[i][0]
        self.mines = self.difficulty[i][1]
        self.geometry(str(self.difficulty[i][2]))

        self.lvl = "SMALL" if i==0 else "MEDIUM" if i==1 else "LARGE"

        self.reset_game()

    def create_widgets(self):
        self.widgets = tk.Frame(self)
        self.widgets.pack()
        self.mVar = tk.StringVar()
        self.mVar.set(self.minesLeft)
        tk.Label(self.widgets, text = "Mines Left: ").pack(side="left")
        tk.Label(self.widgets, textvariable=self.mVar).pack(side="left")

        self.tVar = tk.StringVar()
        self.tVar.set(0)
        tk.Label(self.widgets, text = "Time: ").pack(side="left")
        tk.Label(self.widgets, textvariable=self.tVar).pack(side="left")


    def reset_game(self):
        self.gameOverFlag = True
        self.firstMoveFlag = True
        self.set_minesLeft_and_reset_label()
        
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.buttons = [[None for _ in range(self.size)] for _ in range(self.size)]

        self.placeButtons()
        self.place_mines()
        self.update_numbers()
        
        
    def set_minesLeft_and_reset_label(self):
        self.minesLeft = self.mines
        self.mVar.set(self.minesLeft)

    def placeButtons(self):
        for i in range(self.size):
            for j in range(self.size):
                btn = tk.Button(self.frame, width=2, height=1)
                btn.bind("<Button-1>", lambda e, x=i, y=j: self.on_click(x, y))
                btn.bind("<Button-3>", lambda e, x=i, y=j: self.on_right_click(x, y))
                btn.grid(row=i, column=j)
                self.buttons[i][j] = btn

    def place_mines(self):
        mines_placed = 0
        while mines_placed < self.mines:
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if self.grid[x][y] != -1:
                self.grid[x][y] = -1
                mines_placed += 1

    def update_numbers(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == -1:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        ni, nj = i + dx, j + dy
                        if 0 <= ni < self.size and 0 <= nj < self.size and self.grid[ni][nj] == -1:
                            count += 1
                self.grid[i][j] = count
        

    def check_bomb(self, x, y):
        if self.gameOverFlag or self.buttons[x][y]["text"] == "X":
            return
        if self.grid[x][y] == -1:
            self.buttons[x][y].config(text="*", bg="red")
            self.game_over()
            return True
        return False

    def replace_mine(self,x,y):
        if self.grid[x][y] != -1:
            return
        while True:
            xx = random.randint(0, self.size - 1)
            yy = random.randint(0, self.size - 1)
            if self.grid[xx][yy] != -1:
                self.grid[x][y] = 0
                self.grid[xx][yy] = -1
                self.update_numbers()
                break

    def on_click(self, x, y):
        if self.firstMoveFlag:
            self.start_timer()
            if self.grid[x][y] == -1:
                self.replace_mine(x,y)
            self.firstMoveFlag = False

        self.check_bomb(x,y)
        if self.buttons[x][y]["state"] == "disabled":
            lb = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    ni, nj = x + dx, y + dy
                    if 0 <= ni < self.size and 0 <= nj < self.size and self.buttons[ni][nj]["text"] == "X":
                        lb += 1
            if self.grid[x][y] == lb:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        ni, nj = x + dx, y + dy
                        if 0 <= ni < self.size and 0 <= nj < self.size:
                            if self.check_bomb(ni,nj):
                                return
                            self.reveal(ni,nj)
        else:
            self.reveal(x, y)
        self.check_win()

    def on_right_click(self, x, y):
        if self.gameOverFlag or self.buttons[x][y]["state"] == "disabled":
            return
        btn = self.buttons[x][y]
        if btn["text"] == "X":
            btn.config(text="")
            self.minesLeft+=1
            self.mVar.set(self.minesLeft)
        else:
            btn.config(text="X")
            btn.config()
            self.minesLeft-=1
            self.mVar.set(self.minesLeft)

    def revealAll(self):
        for i in range(self.size):
            for j in range(self.size):
                self.reveal(i,j)

    def reveal(self, x, y):
        button = self.buttons[x][y]
        value = self.grid[x][y]

        if button["state"] == "disabled" or button["text"] == "X":
            return
        button.config(text=str(value) if value > 0 else "", state="disabled", relief=tk.SUNKEN, \
                                  disabledforeground=self.colors[value], \
                                    font = 'sans 9 bold')
        if value == 0:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    ni, nj = x + dx, y + dy
                    if 0 <= ni < self.size and 0 <= nj < self.size:
                        self.reveal(ni, nj)

    def check_win(self):
        if self.gameOverFlag:
            return
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] != -1 and self.buttons[i][j]["state"] != "disabled":
                    return
        self.win()

    def game_over(self):
        self.gameOverFlag = True
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == -1:
                    self.buttons[i][j].config(text="", bg="red")
        self.revealAll()
        self.disable_all_buttons()
        messagebox.showinfo("Game Over", "You hit a mine! Game Over!")

    def win(self):
        self.gameOverFlag = True
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == -1:
                    self.buttons[i][j].config(bg="green")
        self.disable_all_buttons()
        messagebox.showinfo("Congratulations!", "You won the game!")
        self.saveScore()

    def disable_all_buttons(self):
        for row in self.buttons:
            for btn in row:
                btn.config(state="disabled")



if __name__ == "__main__":
    game = Minesweeper()
    game.mainloop()
