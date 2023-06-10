import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { UserStateType } from "../models";

const initialState: UserStateType = {
  csrf_token: "",
  admin: 0,
  company: "",
  country: "",
  department: "",
  email: "",
  name: "",
  purpose: "",
  verified: false,
  isLoggedIn: false,
  position: "",
  id: -1,
  active: null,
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    setUserState: (state, action: PayloadAction<UserStateType>) => {
      //* Set admin value to 0 if admin value is null or undefined
      action.payload.admin === undefined || action.payload.admin === null
        ? (state.admin = 0)
        : (state.admin = action.payload.admin);
      state.company = action.payload.company;
      state.country = action.payload.country;
      state.department = action.payload.department;
      state.email = action.payload.email;
      state.purpose = action.payload.purpose;
      state.verified = action.payload.verified;
      state.isLoggedIn = action.payload.isLoggedIn;
      state.name = action.payload.name;
      state.position = action.payload.position;
      state.id = action.payload.id;
      state.active = action.payload.active;
      state.csrf_token = action.payload.csrf_token;
    },
    setIsLoggedIn: (state, action: PayloadAction<boolean>) => {
      state.isLoggedIn = action.payload;
    },
    setLoggedOut: (state) => {
      state.isLoggedIn = false;
    },
    setCSRF: (state, action: PayloadAction<string>) => {
      console.log(action.payload);
      state.csrf_token = action.payload;
    },
  },
});

export default userSlice.reducer;
export const { setUserState, setLoggedOut, setCSRF, setIsLoggedIn } =
  userSlice.actions;
