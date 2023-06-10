import useAxios from "axios-hooks";
import { useState } from "react";

import { setLoggedOut, setUserState } from "../../store/features/userSlice";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { UserStateType } from "../../store/models";
import { API_URL } from "../templates/api";

/**
 * @returns All redux management related to the user state
 */
const useCurrentUser = (): {
  user: UserStateType;
  setCurrentUser: (user: UserStateType) => void;
  getCSRFToken: any;
  logOut: () => void;
  setLogOutState: () => void;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  loading: boolean;
} => {
  const user = useAppSelector((state) => state.user);
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);

  const [, getCSRFToken] = useAxios(
    {
      url: `${API_URL}/get_csrf_token`,
      withCredentials: true,
    },
    { manual: true }
  );

  // * Post user and log out
  const [, getLogout] = useAxios(
    {
      url: `${API_URL}/logout`,
      withCredentials: true,
    },
    { manual: true }
  );

  // * Setting user state
  const setCurrentUser = (user: UserStateType) => {
    dispatch(setUserState(user));
  };

  // * Post API, set user state to logged out
  const logOut = async () => {
    await getLogout();
    dispatch(setLoggedOut());
  };

  const setLogOutState = async () => {
    dispatch(setLoggedOut());
  };
  return {
    user,
    setCurrentUser,
    logOut,
    loading,
    setLoading,
    getCSRFToken,
    setLogOutState,
  };
};

export default useCurrentUser;
