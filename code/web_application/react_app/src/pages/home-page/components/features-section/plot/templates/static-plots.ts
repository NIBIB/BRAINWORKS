import { brand500 } from "../../../../../../setup/theme/colors";

// * Triples
export const EXAMPLE_TRIPLES = {
  graph: {
    edges: [
      {
        attributes: {
          color: "#A0AEC0",
          label: "associates with",
          size: 5,
          type: "arrow",
        },
        key: "1-2",
        source: "brain",
        target: "omega",
      },
      {
        attributes: {
          color: "#A0AEC0",
          label: "increases",
          size: 5,
          type: "arrow",
        },
        key: "3-1",
        source: "activity",
        target: "brain",
      },
    ],
    // Nodes
    nodes: [
      {
        attributes: {
          color: brand500,
          label: "Brain Health",
          size: 20,
          x: -7,
          y: 0,
        },
        key: "brain",
      },
      {
        attributes: {
          color: brand500,
          label: "Increased Omega3 Intake",
          size: 20,
          x: 0,
          y: 5,
        },
        key: "omega",
      },
      {
        attributes: {
          data: {},
          color: brand500,
          label: "Physical Activity",
          size: 30,
          x: 3,
          y: 0,
        },
        key: "activity",
      },
    ],
  },
};

// * Paper Citations
export const EXAMPLE_PAPER_CITATIONS = {
  graph: {
    edges: [
      {
        attributes: {
          color: "#A0AEC0",
          label: "cited",
          size: 5,
          type: "arrow",
        },
        key: "1-2",
        source: "brain",
        target: "omega",
      },
      {
        attributes: {
          color: "#A0AEC0",
          label: "cited",
          size: 5,
          type: "arrow",
        },
        key: "3-1",
        source: "activity",
        target: "brain",
      },
    ],
    // Nodes
    nodes: [
      {
        attributes: {
          color: brand500,
          label: "Brain health as a global priority",
          size: 20,
          x: 0,
          y: -5,
        },
        key: "brain",
      },
      {
        attributes: {
          color: brand500,
          label: "The Role of Omega-3 Fatty Acid Supplements",
          size: 20,
          x: 5,
          y: 0,
        },
        key: "omega",
      },
      {
        attributes: {
          data: {},
          color: brand500,
          label: "Brain network correlates of physical and mental fitness",
          size: 30,
          x: 0,
          y: 5,
        },
        key: "activity",
      },
      {
        attributes: {
          data: {},
          color: brand500,
          label: "Physical Activity",
          size: 30,
          x: 5,
          y: 4,
        },
        key: "activity",
      },
    ],
  },
};

// * Topic CoOccurences
export const EXAMPLE_TOPIC_CO_OCCURENCES = {
  graph: {
    edges: [
      {
        attributes: {
          color: "#A0AEC0",
          label: "",
          size: 5,
        },
        key: "1-2",
        source: "brain",
        target: "arm",
      },
      {
        attributes: {
          color: "#A0AEC0",
          label: "",
          size: 5,
        },
        key: "3-1",
        source: "leg",
        target: "brain",
      },
      {
        attributes: {
          color: "#A0AEC0",
          label: "",
          size: 5,
        },
        key: "neuron-brain",
        source: "neuron",
        target: "brain",
      },
      {
        attributes: {
          color: "#A0AEC0",
          label: "",
          size: 5,
        },
        key: "mumscle-brain",
        source: "muscle",
        target: "brain",
      },
    ],
    // Nodes
    nodes: [
      {
        attributes: {
          color: brand500,
          label: "Brain",
          size: 15,
          x: 0,
          y: 0,
        },
        key: "brain",
      },
      {
        attributes: {
          color: brand500,
          label: "Arm",
          size: 10,
          x: 0,
          y: 0,
        },
        key: "arm",
      },
      {
        attributes: {
          data: {},
          color: brand500,
          label: "Leg",
          size: 10,
          x: 0,
          y: 0,
        },
        key: "leg",
      },
      {
        attributes: {
          data: {},
          color: brand500,
          label: "Neuron",
          size: 15,
          x: 0,
          y: 0,
        },
        key: "neuron",
      },
      {
        attributes: {
          data: {},
          color: brand500,
          label: "Muscle",
          size: 10,
          x: 0,
          y: 0,
        },
        key: "muscle",
      },
    ],
  },
};
