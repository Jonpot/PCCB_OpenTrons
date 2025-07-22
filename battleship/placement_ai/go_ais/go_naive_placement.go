package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"sort"
)

type ShipSpec struct {
	Length int `json:"length"`
	Count  int `json:"count"`
}

type Placement struct {
	Row       int    `json:"row"`
	Col       int    `json:"col"`
	Length    int    `json:"length"`
	Direction string `json:"direction"`
}

type Config struct {
	BoardShape []int               `json:"board_shape"`
	ShipSchema map[string]ShipSpec `json:"ship_schema"`
}

// PlacementGenerator must be implemented by Go placement AIs.
type PlacementGenerator interface {
	GeneratePlacement(boardShape []int, shipSchema map[string]ShipSpec) []Placement
}

// RunPlacementAI handles I/O for placement AIs.
func RunPlacementAI(ai PlacementGenerator) {
	if len(os.Args) < 2 {
		fmt.Print("[]")
		return
	}
	data, err := ioutil.ReadFile(os.Args[1])
	if err != nil {
		fmt.Print("[]")
		return
	}
	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		fmt.Print("[]")
		return
	}
	placements := ai.GeneratePlacement(cfg.BoardShape, cfg.ShipSchema)
	out, err := json.Marshal(placements)
	if err != nil {
		fmt.Print("[]")
		return
	}
	fmt.Print(string(out))
}

// NaivePlacement is a deterministic placement generator used as an example.
type NaivePlacement struct{}

func (NaivePlacement) GeneratePlacement(boardShape []int, shipSchema map[string]ShipSpec) []Placement {
	if len(boardShape) != 2 {
		return nil
	}
	rows, cols := boardShape[0], boardShape[1]
	var placements []Placement
	curRow, curCol := 0, 0

	names := make([]string, 0, len(shipSchema))
	for name := range shipSchema {
		names = append(names, name)
	}
	sort.Strings(names)

	for _, name := range names {
		spec := shipSchema[name]
		for i := 0; i < spec.Count; i++ {
			if curCol+spec.Length > cols {
				curRow++
				curCol = 0
				if curRow >= rows {
					goto done
				}
			}
			placements = append(placements, Placement{
				Row:       curRow,
				Col:       curCol,
				Length:    spec.Length,
				Direction: "horizontal",
			})
			curCol += spec.Length + 1
		}
	}

done:
	return placements
}

func main() {
	RunPlacementAI(NaivePlacement{})
}
