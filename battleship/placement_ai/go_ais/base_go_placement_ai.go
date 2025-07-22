package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
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
