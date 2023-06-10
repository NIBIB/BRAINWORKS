import { ChakraProvider, useDisclosure } from "@chakra-ui/react";
import axios from "axios";
import Router from "./setup/Router";
import ConfirmContextProvider from "./store/features/confirmContext";
import GlobalConfirmModal from "./common/components/GlobalConfirmModal";
import useCurrentUser from "./common/hooks/useCurrentUser";
import { theme } from "./setup/theme/theme";
import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { ParallaxProvider } from "react-scroll-parallax";
import IdleTimerContextProvider from "store/features/IdleTimerContext";
import ActivityTimer from "setup/ActivityTimer";
import { API_URL } from "common/templates/api";

// TODO:  clean this up
export const App = () => {
  // TODO: clean this up use useaxios move somewhere else

  const { user, setCurrentUser } = useCurrentUser();
  const [loading, setLoading] = useState(true);
  const { isOpen, onOpen, onClose } = useDisclosure();

  useEffect(() => {
    const test = async () => {
      const response = await axios.get(`${API_URL}/user_session`, {
        withCredentials: true,
        headers: {
          "Content-Type": "application/json",
        },
      });
      setCurrentUser(response.data);
      setLoading(false);
    };
    test();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ChakraProvider theme={theme}>
      <BrowserRouter>
        <ParallaxProvider>
          <ConfirmContextProvider>
            <IdleTimerContextProvider>
              <GlobalConfirmModal
                onClose={onClose}
                isOpen={isOpen}
                onOpen={onOpen}
              />

              {!loading && (
                <>
                  {/* If the user is logged in, start the activity timer */}
                  {user.isLoggedIn && <ActivityTimer />}
                  <Router />
                </>
              )}
            </IdleTimerContextProvider>
          </ConfirmContextProvider>
        </ParallaxProvider>
      </BrowserRouter>
    </ChakraProvider>
  );
};
