import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import useAPIDataAlert from "../../../common/hooks/useAPIDataAlert";
import LoadingVisualScreen from "./components/manage/LoadingVisualScreen";
import VisualizerRouter from "./components/manage/VisualizerRouter";
import useCurrentVisualizer from "../hooks/useCurrentVisualizer";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";
import useGlobalAlert from "common/hooks/useGlobalAlert";

/**
 *
 */
const VisualizerEditor = () => {
  const navigate = useNavigate();
  const { getAxios: getToolData } = useAxiosWrapper({
    url: `visualizer-editor`,
    method: "GET",
  });

  const { apiDataAlerter } = useAPIDataAlert();
  const { setCurrentVisualizer } = useCurrentVisualizer();
  const [loading, setLoading] = useState(true);
  const { showGlobalAlert } = useGlobalAlert();

  useEffect(() => {
    const buildVisual = async () => {
      const { data } = await getToolData();
      apiDataAlerter({
        data: data,
        onSuccess: () => {
          setCurrentVisualizer(data.success);
          setLoading(false);
        },
        onFailure: () => {
          navigate("/");
        },
      });
    };
    try {
      buildVisual();
    } catch {
      showGlobalAlert(
        "Something went wrong!",
        "The request to create your visual could not send."
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <>{loading ? <LoadingVisualScreen /> : <VisualizerRouter />}</>;
};

export default VisualizerEditor;
