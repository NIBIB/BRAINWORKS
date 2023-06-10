import { Input } from "@chakra-ui/react";
import { VisualizerSelectionType } from "./models";

/**
 * Visualizer pages templates
 *
 * Add/edit existing tool option to dynamically change the tool selection and tool form pages
 */

/**
 * VISUALIZER_SELECTION
 *
 * Object that contains information for the tool selection card on the `/create` page
 *
 * * `title` - Title of tool
 * * `desc` - Short description of tool
 * * `img` - Route to the image source
 * * `route` - URL for the form acts as key in the `VISUALIZER_FORMS` object
 */
export const VISUALIZER_SELECTION: VisualizerSelectionType[] = [
  {
    title: "Topic Co-occurrences",
    desc: "Track trends by observing the occurrences of connected topics in the literature.",
    img: "topic-co-occurrences-cover.png",
    route: "topic_co_occurrences",
  },
  {
    title: "Triples",
    desc: "Surface patterns through pairing of findings across papers.",
    img: "triples-cover.png",
    route: "triples",
  },
  {
    title: "Paper Triples",
    desc: "Extract a paper's key findings into structured semantic triples.",
    img: "paper-triples-cover.png",
    route: "paper_triples",
  },
  {
    title: "Paper Citations",
    desc: "Find the origin of a specific topic by tracing its citations.",
    img: "paper-citations-cover.png",
    route: "paper_citations",
  },
];

/***
 * VISUALIZER_FORMS
 *
 * Object that contains React components for the required fields and optional fields. These fields will be mapped at the `VisualizerForms` component. Key of dictionary is the tool's name / route in `VISUALIZER_SELECTION`.
 *
 * * `formKey` - Matches to the Flask form's key dictionary to determine what form will be rendered
 * * `required` - Array of React components, specifically field components
 * * `optional` - Array of React components, specifically field components, leave empty if there are no optional fields
 *
 */
export const VISUALIZER_FORMS: any = {
  // Paper triples
  paper_triples: {
    title: "Paper Triples",
    img: "paper-triples-cover.png",
    desc: "Extract a paper's key findings into structured semantic triples.",
    formKey: "tool_paper_triples_form",
    required: [
      {
        property: "pmid",
        fieldType: Input,
      },
    ],
    optional: [],
  },
  // Topic co-occurrences
  topic_co_occurrences: {
    title: "Topic Co-occurences",
    img: "topic-co-occurrences-cover.png",
    desc: "Track trends by observing the occurrences of connected topics in the literature.",
    formKey: "tool_topic_co_occurrences_form",
    required: [
      {
        property: "include_mesh_concepts",
        fieldType: "stringArray",
      },
    ],
    optional: [
      {
        property: "exclude_mesh_concepts",
      },
      {
        property: "limit",
      },
    ],
  },
  // Paper Citations
  paper_citations: {
    title: "Paper Citations",
    img: "paper-citations-cover.png",
    desc: "Find the origin of a specific topic by tracing its citations.",
    formKey: "tool_paper_citations_form",
    required: [
      {
        property: "include_concepts",
      },
    ],
    optional: [
      {
        property: "limit",
      },
    ],
  },
  // Triples
  triples: {
    title: "Triples",
    img: "triples-cover.png",
    desc: "Surface patterns through pairing of findings across papers.",
    formKey: "tool_triples_form",
    required: [
      {
        property: "include_concepts",
      },
    ],
    optional: [
      {
        property: "exclude_concepts",
      },
      {
        property: "limit",
      },
    ],
  },
};
