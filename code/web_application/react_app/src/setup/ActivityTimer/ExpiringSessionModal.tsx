import { IIdleTimer } from "react-idle-timer";
import {
  Button,
  HStack,
  Modal,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react";
import { brandColorScheme } from "setup/theme/colors";
import { useEffect, useState } from "react";

interface AppProps {
  idleTimer: IIdleTimer;
  isOpen: boolean;
  handleSessionReturn: () => void;
  handleEndSession: () => void;
}

/**
 * ExpiringSessionModal
 *
 * React component that renders a modal that countdowns until the session will expire automatically
 */
const ExpiringSessionModal = ({
  idleTimer,
  handleSessionReturn,
  isOpen,
  handleEndSession,
}: AppProps) => {
  const [timeoutCount, setTimeoutCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeoutCount(Math.floor(idleTimer.getRemainingTime() / 1000));
    }, 1000);
    return () => {
      clearInterval(interval);
    };
  }, [idleTimer]);

  return (
    <Modal onClose={handleSessionReturn} isOpen={isOpen} isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          Your session expires in {timeoutCount} seconds
        </ModalHeader>
        <ModalCloseButton />
        <ModalFooter>
          <HStack>
            <Button onClick={handleEndSession}>Log out</Button>
            {timeoutCount > 0 && (
              <Button
                onClick={handleSessionReturn}
                colorScheme={brandColorScheme}
              >
                Return to session
              </Button>
            )}
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ExpiringSessionModal;
