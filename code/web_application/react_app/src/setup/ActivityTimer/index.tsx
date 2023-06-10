import { useDisclosure, useToast } from "@chakra-ui/react";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";
import { useIdleTimer } from "react-idle-timer";
import { setLoggedOut } from "store/features/userSlice";
import { useAppDispatch } from "store/hooks";
import ExpiringSessionModal from "./ExpiringSessionModal";

// * Timeout in seconds
const EXPIRE_TIMER = 115 * 60; // 115 minutes of inactivity
const PROMPT_TIMER = 300; // 5 minute til expire prompt

/**
 * ActivityTimer
 *
 * Opens a prompt after 15 minutes of inactivity, the prompt stays for 5 minutes
 *
 * Activity is considered when the user switches pages or makes a request to the API
 */
const ActivityTimer = () => {
  const toast = useToast();
  const dispatch = useAppDispatch();

  const { getAxios: getSessionResume } = useAxiosWrapper({
    url: "resume_session",
    method: "GET",
  });

  const { getAxios: getLogout } = useAxiosWrapper({
    url: "logout",
    method: "GET",
  });

  const handleSessionReturn = async () => {
    // * Pings backend to resume session
    await getSessionResume();
    // * Reset timer session
    idleTimer.reset();
    // * Close modal
    onClose();
  };

  // * Handles ending the session
  const handleEndSession = async () => {
    const { data } = await getLogout();
    console.log("Ending session activity timer");
    // * If session has already expired, this will display the message in the API wrapper
    if (data?.success === "Logged out") {
      dispatch(setLoggedOut());
      toast({
        title: `Your session may have expired`,
        description: `You have been logged out of your account.`,
        status: "warning",
        duration: null,
        isClosable: true,
        position: "top",
      });
    }
    onClose();
  };

  // * Handle opening idle modal
  const onIdle = () => {
    handleEndSession();
  };

  // * Handle opening idle modal
  const onPrompt = () => {
    onOpen();
  };

  const idleTimer = useIdleTimer({
    onPrompt,
    onIdle,
    promptTimeout: 1000 * PROMPT_TIMER,
    timeout: 1000 * EXPIRE_TIMER,
    events: [],
  });

  const { onClose, isOpen, onOpen } = useDisclosure();

  return (
    <ExpiringSessionModal
      idleTimer={idleTimer}
      isOpen={isOpen}
      handleSessionReturn={handleSessionReturn}
      handleEndSession={handleEndSession}
    />
  );
};

export default ActivityTimer;
