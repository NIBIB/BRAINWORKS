import { containsError, containsSuccess } from "../utils";
import useGlobalFormik from "./useGlobalFormik";
import useGlobalAlert from "./useGlobalAlert";

interface PostWrapperFunctionProps {
  data: any;
  onSuccess?: () => void;
  successMsg?: string;
  onFailure?: () => void;
  failureMsg?: string;
}

/**
 * React hook that helps reduce redundant code when posting with `useAxios` to the BRAINWORKS API. It ultizes `useGlobalAlert` and and try and catch statements to help error check
 *
 * If JSON returns `success` or `error` it prints that message, otherwise it prints out success/error message from the API
 *
 * If request fails, then it prints out generic error message
 */
const useAPIDataAlert = (): {
  /**
   * Function that reduces redunancy of interpretting a JSON from the BRAINWORKS API
   */
  apiDataAlerter: ({
    onSuccess,
    successMsg,
    onFailure,
    failureMsg,
    data,
  }: PostWrapperFunctionProps) => Promise<void>;
  /**
   * Function that returns a standard error message
   */
  standardAlertError: () => void;
  /**
   * Function that puts a try catch statement around the given function, if there are errors it throws the standard alert error
   */
  tryCatchWrapper: (func: any) => void;
} => {
  const { showGlobalAlert } = useGlobalAlert();
  const { formikSlice, newCaptcha } = useGlobalFormik();

  const standardAlertError = () => {
    showGlobalAlert("Something went wrong!", "Please try again later");
  };

  const tryCatchWrapper = (func: any) => {
    try {
      func();
    } catch {
      standardAlertError();
    }
  };

  const apiDataAlerter = async ({
    onSuccess,
    successMsg,
    onFailure,
    failureMsg,
    data,
  }: PostWrapperFunctionProps) => {
    if (containsSuccess(data)) {
      // * If object contains "success", alert either custom success message or one from back end
      if (successMsg) {
        showGlobalAlert("Success!", successMsg, "success");
      } else {
        if (typeof data.success === "string") {
          showGlobalAlert("Success!", data.success, "success");
        }
      }
      // * Run success function, if one is defined
      if (onSuccess) {
        onSuccess();
      }
    } else {
      // * If object contains "error", alert either custom failure message or one from back end
      if (containsError(data)) {
        if (failureMsg) {
          showGlobalAlert("Something went wrong!", failureMsg, "error");
        } else {
          showGlobalAlert("Something went wrong!", data.error);
        }
        // * If form has CAPTCHA, checking if image is set, if so set a new captcha
        if (formikSlice.captcha.img.length > 0) {
          newCaptcha();
        }
      }
      // * Run failure function, if one is define
      if (onFailure) {
        onFailure();
      }
    }
  };

  return { apiDataAlerter, standardAlertError, tryCatchWrapper };
};

export default useAPIDataAlert;
