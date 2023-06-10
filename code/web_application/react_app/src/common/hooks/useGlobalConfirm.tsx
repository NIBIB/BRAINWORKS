import { useContext } from "react";
import { ConfirmContext } from "../../store/features/confirmContext";
import { ShowConfirmType } from "../../store/models";

/**
 * @returns state to hide or show global alert system
 */
// TODO: clean this up like the status
const useGlobalConfirm = (): {
  onGlobalConfirmOpen: () => void;
  onGlobalConfirmClose: () => void;
  showGlobalConfirm: ({
    title,
    desc,
    confirm,
    unconfirm,
  }: ShowConfirmType) => void;
} => {
  const appContext = useContext(ConfirmContext);

  const showGlobalConfirm = ({
    title,
    desc,
    confirm,
    unconfirm,
  }: ShowConfirmType) => {
    if (appContext.setConfirm) {
      appContext.setConfirm((prevState) => {
        return {
          ...prevState,
          title: title,
          desc: desc,
          confirm: confirm,
          unconfirm: unconfirm,
        };
      });
    }
  };

  const onGlobalConfirmOpen = () => {
    if (appContext.confirm && appContext.confirm.onOpen) {
      appContext.confirm.onOpen();
    }
  };

  const onGlobalConfirmClose = () => {
    if (appContext.confirm && appContext.confirm.onClose) {
      appContext.confirm.onClose();
    }
  };

  return { onGlobalConfirmOpen, onGlobalConfirmClose, showGlobalConfirm };
};

export default useGlobalConfirm;
