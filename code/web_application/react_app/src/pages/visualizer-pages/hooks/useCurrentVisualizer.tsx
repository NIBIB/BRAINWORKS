import { setVisualizerData } from "../../../store/features/visualizerSlice";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";

/**
 * useCurrentVisualizer
 *
 * React hook that returns the current visualizer's data generated from the backend
 */
const useCurrentVisualizer = (): {
  setCurrentVisualizer: (data: any) => void;
  curVisualizer: any;
} => {
  const dispatch = useAppDispatch();
  const curVisualizer = useAppSelector((state) => state.visualizer);

  const setCurrentVisualizer = (data: any) => {
    dispatch(setVisualizerData(data));
  };

  return { setCurrentVisualizer, curVisualizer };
};

export default useCurrentVisualizer;
