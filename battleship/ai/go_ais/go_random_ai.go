package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"os"
	"time"
)

// Board represents the board state as a 2-D array of ints.
type Board [][]int

// MoveSelector defines the required method for a Battleship Go AI.
type MoveSelector interface {
	SelectNextMove(board Board) (int, int)
}

// RunAI handles all I/O for a Go AI. It reads the board from the file path
// provided as the first command line argument, calls the AI's SelectNextMove
// method, and prints the chosen row and column to stdout.
func RunAI(ai MoveSelector) {
	if len(os.Args) < 2 {
		fmt.Printf("0 0")
		return
	}
	data, err := ioutil.ReadFile(os.Args[1])
	if err != nil {
		fmt.Printf("0 0")
		return
	}
	var board Board
	if err := json.Unmarshal(data, &board); err != nil {
		fmt.Printf("0 0")
		return
	}
	r, c := ai.SelectNextMove(board)
	fmt.Printf("%d %d", r, c)
}

// RandomAI is a simple example implementation that chooses randomly among
// unknown cells on the board.
type RandomAI struct{}

func (r *RandomAI) SelectNextMove(board Board) (int, int) {
	var unknowns [][2]int
	for i, row := range board {
		for j, cell := range row {
			if cell == 0 { // WellState.UNKNOWN
				unknowns = append(unknowns, [2]int{i, j})
			}
		}
	}
	if len(unknowns) == 0 {
		return 0, 0
	}
	rand.Seed(time.Now().UnixNano())
	pick := unknowns[rand.Intn(len(unknowns))]
	return pick[0], pick[1]
}

func main() {
	RunAI(&RandomAI{})
}
