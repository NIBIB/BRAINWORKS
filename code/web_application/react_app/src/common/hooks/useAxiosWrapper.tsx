import { useToast } from "@chakra-ui/react";
import useAxios from "axios-hooks";
import { API_URL } from "common/templates/api";
import { setIsLoggedIn } from "store/features/userSlice";
import { useAppDispatch } from "store/hooks";
import useCurrentUser from "./useCurrentUser";

interface RenderProps {
  getAxios: () => Promise<any>;
  postAxios: (givenData: any | undefined) => Promise<any>;
}

interface AppProps {
  url: string;
  method?: "GET" | "POST";
}

/**
 * useAxiosWrapper
 *
 * React hook that wraps around `useAxios` hook.
 *
 * Before it calls the request the most recent CSRF token in the session before it submits the the fetch request. It needs to do this in order to avoid CSRF errors.
 *
 * Every fetch request resets the activity timer to match to the Flask activity
 *
 * Every request also sets the user's login state
 *
 * `url` - begins with `api/`
 */
const useAxiosWrapper = ({ url, method }: AppProps): RenderProps => {
  const dispatch = useAppDispatch();
  const { user } = useCurrentUser();
  const toast = useToast();

  // * Fetch to see if user is logged in or not
  const [, getLoginStatus] = useAxios(
    {
      url: `${API_URL}/get_auth_status`,
      withCredentials: true,
    },
    { manual: true }
  );

  // * Fetch to get most recent CSRF token
  const [, getCSRFToken] = useAxios(
    {
      url: `${API_URL}/get_csrf_token`,
      withCredentials: true,
    },
    { manual: true }
  );

  // * Fetch function to get data from URL
  const [, refetch] = useAxios(
    {
      url: `${API_URL}/${url}`,
      method: method === undefined ? "GET" : method,
    },
    { manual: true }
  );

  // * For every fetch request reset activity timer, get most current CSRF token and login status and see if the session has expired
  const checkUserStatus = async () => {
    const { data: token } = await getCSRFToken();
    const { data: sessionLoggedIn } = await getLoginStatus();

    // * If the user is logged in on the front end and the session says the user is not logged in, log user out
    if (user.isLoggedIn && !sessionLoggedIn?.success) {
      console.log("Session may have expired from axios wrapper");
      toast({
        title: `Your session may have expired`,
        description: `You have been logged out of your account.`,
        status: "warning",
        duration: null,
        isClosable: true,
        position: "top",
      });
    }
    dispatch(setIsLoggedIn(sessionLoggedIn?.success));
    return { token };
  };

  const getAxios = async () => {
    const { token } = await checkUserStatus();
    if (method === "GET") {
      return refetch({
        withCredentials: true,
        headers: {
          "X-CSRFToken": token?.success,
          "Content-Type": "application/json",
        },
      });
    }
  };
  // * Gets current CSRF token before the fetch request
  const postAxios = async (givenData: any | undefined) => {
    const { token } = await checkUserStatus();
    if (method === "POST") {
      return await refetch({
        data: {
          ...givenData,
        },
        withCredentials: true,
        headers: {
          "X-CSRFToken": token?.success,
          "Content-Type": "application/json",
        },
      });
    }
  };
  return { getAxios, postAxios };
};

export default useAxiosWrapper;
