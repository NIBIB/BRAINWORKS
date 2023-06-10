import useCurrentUser from "./useCurrentUser";

/***
 * useAxiosConfig
 *
 * React hook returns axios config that allows for cookies & csrf token
 */
const useAxiosConfig = (): {
  config: {
    withCredentials: boolean;
    headers: any;
  };
} => {
  const { user } = useCurrentUser();

  return {
    config: {
      withCredentials: true,
      headers: {
        "X-CSRFToken": user.csrf_token,
        "Content-Type": "application/json",
      },
    },
  };
};

export default useAxiosConfig;
