import { configureStore } from "@reduxjs/toolkit";
import alertSlice from "./features/alertSlice";
import userSlice from "./features/userSlice";
import formikSlice from "./features/formikSlice";
import visualizerSlice from "./features/visualizerSlice";

const store = configureStore({
  reducer: {
    alert: alertSlice,
    user: userSlice,
    formik: formikSlice,
    visualizer: visualizerSlice,
  },
});

export default store;
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
