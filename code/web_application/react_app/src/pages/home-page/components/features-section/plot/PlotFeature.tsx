import { useEffect, useState } from "react";
import { FiCalendar, FiFile, FiSearch } from "react-icons/fi";
import Feature from "../blocks/Feature";
import PlotVisual from "./PlotVisual";

const FEATURES = [
  {
    text: "Surface patterns through automated pairings of findings across papers.",
    icon: <FiFile />,
  },
  {
    text: "Find the origin of a specific topic by tracing its citations.",
    icon: <FiSearch />,
  },
  {
    text: "Observe current trends through topics correlated over time.",
    icon: <FiCalendar />,
  },
];

const INTERVAL = 7000;
const NUM_OF_PLOT = 3;

const PlotFeature = () => {
  const [carousel, setCarousel] = useState(0);
  const [stop, setStop] = useState(false);

  useEffect(() => {
    if (stop) {
      return;
    }
    const timer = setTimeout(() => {
      if (!stop) {
        if (carousel < NUM_OF_PLOT - 1) {
          setCarousel((prevState) => prevState + 1);
        } else {
          setCarousel(0);
        }
      }
    }, INTERVAL);

    return () => {
      clearTimeout(timer);
    };
  }, [carousel, stop]);

  return (
    <Feature
      features={FEATURES}
      line1={"Connect"}
      line2={" topics."}
      desc={
        "Illustrate and indentify connections across a collection of published scientific papers."
      }
      subFeatureState={carousel}
      setSubFeatureState={setCarousel}
      setStop={setStop}
      visual={<PlotVisual setStop={setStop} stop={stop} carousel={carousel} />}
    />
  );
};

export default PlotFeature;
