import { createSlice, PayloadAction } from "@reduxjs/toolkit";

const initialState: any = {
  key: "",
  loading: false,
  fieldsInfo: [],
  captcha: { img: "", audio: "" },
};

/**
 * formikSlice
 *
 * Redux slice that holds additional information about the formik form including
 */
const formikSlice = createSlice({
  name: "formikSlice",
  initialState,
  reducers: {
    setFormikSlice: (state, action: PayloadAction<any>) => {
      state.key = action.payload.key;
      state.loading = action.payload.loading;
      state.fieldsInfo = action.payload.fieldsInfo;
    },
    setNewCaptcha: (state, action: PayloadAction<any>) => {
      state.captcha.img = action.payload.img;
      state.captcha.audio = action.payload.audio;
    },
    resetFormikSlice: (state) => {
      state.key = "";
      state.loading = true;
      state.fieldsInfo = [];
      state.captcha = { img: "", audio: "" };
    },
  },
});

export default formikSlice.reducer;
export const { setFormikSlice, setNewCaptcha, resetFormikSlice } =
  formikSlice.actions;
