import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { AlertType, ShowAlertType } from "../models";

// TODO: put these interfaces somewhere else

const initialState: AlertType = {
  title: "",
  desc: "",
  enabled: false,
  status: "error",
};

const alertSlice = createSlice({
  name: "alert",
  initialState,
  reducers: {
    showAlert: (state, action: PayloadAction<ShowAlertType>) => {
      state.title = action.payload.title;
      state.desc = action.payload.desc;
      state.status = action.payload.status;
      state.enabled = true;
      return state;
    },
    hideAlert: (state) => {
      state.enabled = false;
      state.status = undefined;
      return state;
    },
  },
});

export default alertSlice.reducer;
export const { showAlert, hideAlert } = alertSlice.actions;
