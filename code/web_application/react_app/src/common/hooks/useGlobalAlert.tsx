import { useToast } from "@chakra-ui/react";
import { hideAlert, showAlert } from "../../store/features/alertSlice";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { AlertType, ShowAlertType } from "../../store/models";

/**
 * @returns state to hide or show global alert system
 */

type ShowGlobalAlertType = (
  title: string,
  desc: string,
  status?: "error" | "info" | "warning" | "success" | "loading" | undefined,
  duration?: number | null
) => void;

// TODO: clean this up like the status
const useGlobalAlert = (): {
  globalAlert: AlertType;
  showGlobalAlert: ShowGlobalAlertType;
  hideGlobalAlert: () => void;
} => {
  const globalAlert = useAppSelector((state) => state.alert);
  const dispatch = useAppDispatch();
  const toast = useToast();

  const showGlobalAlert: ShowGlobalAlertType = (
    title,
    desc,
    status,
    duration
  ) => {
    const alert: ShowAlertType = {
      title: title,
      desc: desc,
      status: status ? status : "error",
    };
    dispatch(showAlert(alert));
    toast({
      position: "top",
      title: title,
      description: desc,
      status: status !== undefined ? status : "error",
      duration: duration !== undefined ? duration : 5000,
      isClosable: true,
    });
  };

  const hideGlobalAlert = () => {
    dispatch(hideAlert());
  };

  return { globalAlert, showGlobalAlert, hideGlobalAlert };
};

export default useGlobalAlert;
