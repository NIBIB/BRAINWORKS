import { FiAlignLeft, FiList, FiTrendingUp } from "react-icons/fi";
import Feature from "../blocks/Feature";
import PaperVisual from "./PaperVisual";

const FEATURES = [
  {
    text: "Get the gist of your paper's key points before reading the full paper.",
    icon: <FiTrendingUp />,
  },
  {
    text: "Structure knowledge using established clinical ontologies (ULMS).",
    icon: <FiList />,
    link: "https://www.nlm.nih.gov/research/umls/index.html",
  },
  {
    text: "Navigate key findings with ease, through highlights of paper sections.",
    icon: <FiAlignLeft />,
  },
];

const PaperFeature = () => {
  return (
    <Feature
      features={FEATURES}
      line1={"Synthesize"}
      line2={" findings."}
      desc={
        "Extract a paper's key findings into an interactive table, where sentences are distilled into structured semantic triples (subject, relation, and object)."
      }
      visual={<PaperVisual />}
    />
  );
};

export default PaperFeature;
