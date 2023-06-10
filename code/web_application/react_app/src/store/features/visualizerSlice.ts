import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type VisualizerType = any;

const initialState: VisualizerType = {};

const visualizerSlice = createSlice({
  name: "visualizer",
  initialState,
  reducers: {
    setVisualizerData: (state, action: PayloadAction<any>) => {
      return { ...action.payload };
    },
  },
});

export default visualizerSlice.reducer;
export const { setVisualizerData } = visualizerSlice.actions;
