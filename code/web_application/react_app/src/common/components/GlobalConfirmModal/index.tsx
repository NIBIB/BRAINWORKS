import {
  Button,
  HStack,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react";
import { useContext, useEffect } from "react";
import { ConfirmContext } from "../../../store/features/confirmContext";

interface AppProps {
  onClose: () => void;
  onOpen: () => void;
  isOpen: boolean;
}
const GlobalConfirmModal = ({ onClose, isOpen, onOpen }: AppProps) => {
  const contextCxt = useContext(ConfirmContext);

  useEffect(() => {
    if (contextCxt.setConfirm) {
      contextCxt.setConfirm((prevState) => {
        return { ...prevState, onOpen: onOpen, onClose: onClose };
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCancel = () => {
    if (contextCxt.confirm && contextCxt.confirm.unconfirm) {
      contextCxt.confirm.unconfirm();
    }
    onClose();
  };
  const handleConfirm = () => {
    if (contextCxt.confirm && contextCxt.confirm.confirm) {
      contextCxt.confirm.confirm();
    }
    onClose();
  };
  return (
    <>
      <Modal onClose={onClose} isOpen={isOpen} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{contextCxt.confirm?.title}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>{contextCxt.confirm?.desc}</ModalBody>
          <ModalFooter>
            <HStack align="flex-end" spacing={5}>
              <Button onClick={handleCancel}>Cancel</Button>
              <Button onClick={handleConfirm} colorScheme="red">
                Confirm
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};
export default GlobalConfirmModal;
