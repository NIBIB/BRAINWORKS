import { VISUALIZER_SELECTION } from "./templates";

/**
 * findVisualizerInfo
 *
 * Function that gives the visualizer card info given the representation name
 */
export const findVisualizerInfo = (representation: string) => {
  return VISUALIZER_SELECTION.find((tool) => tool.route === representation);
};

// * Create triple object, with key topic fragments, and associated color and definition
function create_trimmed_triple(
  fragments: any,
  text: any,
  topics: any,
  colors: any
) {
  if (!topics) return;
  // sort topics by the starting character
  let topicsForSort = [...topics];
  topicsForSort.sort((a, b) =>
    a.frag_start_char > b.frag_start_char ? 1 : -1
  );
  let prev = 0; // previous character position in the original text
  for (let topic of topicsForSort) {
    let name = topic.concept_name;
    let def = topic.definition || "No definition available";
    let start = topic.frag_start_char; // original text start pos
    let end = topic.frag_end_char; // original text end pos
    let frag = text.slice(start, end); // next fragment
    let between = text.slice(prev, start); // content between last fragment and new fragment
    if (between.length > 1) {
      fragments.push({ text: between });
    }
    fragments.push({ text: frag, color: colors[name], def: def });
    prev = end; // set prev pos to end of new fragment
  }
}

// * Generate a color map for the TRIPLES (keys are topic names)
export function generate_colors(triples: any) {
  let map: any = {};
  for (let triple of triples) {
    let topics = triple["subject_topics"].concat(triple["object_topics"]); // all topics
    for (let topic of topics) {
      if (!topic) continue;
      let r = Math.floor(Math.random() * 80 + 175).toString(16).padStart(2, "0");
      let g = Math.floor(Math.random() * 80 + 175).toString(16).padStart(2, "0");
      let b = Math.floor(Math.random() * 80 + 175).toString(16).padStart(2, "0");
      map[topic.concept_name] = "#" + r + g + b;
    }
  }
  return map;
}

// * Generates triple array to be rendered
export const createTriplesTable = (triples: any) => {
  let i = 0;
  let colors = generate_colors(triples);
  const trimmedTriples: any = [];
  // * For each triple, generate a triple object
  triples.forEach((triple: any) => {
    const trimmedTriple = {
      subFrags: [],
      relation: "",
      objFrags: [],
      target: `[data-index='${i}']`,
    };
    trimmedTriple.relation = triple.relation;
    let subjects = triple["subject_topics"];
    let objects = triple["object_topics"];

    create_trimmed_triple(
      trimmedTriple.subFrags,
      triple.subject,
      subjects,
      colors
    );
    create_trimmed_triple(
      trimmedTriple.objFrags,
      triple.object,
      objects,
      colors
    );
    trimmedTriples.push(trimmedTriple);
    i++;
  });
  return trimmedTriples;
};
