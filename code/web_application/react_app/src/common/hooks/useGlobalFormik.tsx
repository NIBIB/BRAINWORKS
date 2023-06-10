import useAxios from "axios-hooks";

import {
  resetFormikSlice,
  setFormikSlice,
  setNewCaptcha,
} from "../../store/features/formikSlice";
import { FormikSliceType } from "../../store/models";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { API_URL } from "../templates/api";
interface useFormikSliceReturnType {
  formikSlice: any;
  setFormik: (state: FormikSliceType) => void;
  setCaptcha: any;
  newCaptcha: any;
  resetGlobalFormik: any;
}

/**
 * useGlobalFormik
 *
 * React hook that passes additional information globally for the formik forms
 */
const useGlobalFormik = (): useFormikSliceReturnType => {
  const dispatch = useAppDispatch();
  const formikSlice = useAppSelector((state) => state.formik);

  /**
   * getNewCaptcha
   *
   * Axios get request to get new information for the CAPTCHA
   */
  const [, getNewCaptcha] = useAxios(
    {
      url: `${API_URL}/new_captcha`,
      withCredentials: true,
    },
    { manual: true }
  );

  /**
   * resetGlobalFormik
   *
   * Redux reducer wrapper that resets the formikSlice to its initial values
   */
  const resetGlobalFormik = () => {
    dispatch(resetFormikSlice());
  };

  /**
   * setCaptcha
   *
   * Redux reducer wrapper that sets current CAPTCHA information in formikSlice
   */
  const setCaptcha = (img: string, audio: string) => {
    dispatch(setNewCaptcha({ img: img, audio: audio }));
  };

  /**
   * setFormik
   *
   * Function that wraps formikSlice dispatch
   */
  const setFormik = ({ key, fieldsInfo, loading }: FormikSliceType) => {
    dispatch(
      setFormikSlice({
        key,
        fieldsInfo,
        loading,
      })
    );
  };

  /**
   * newCaptcha
   *
   * Function that makes a get request to get a new captcha img & audio
   */
  const newCaptcha = async () => {
    const { data } = await getNewCaptcha();
    if (data) {
      setCaptcha(data.img, data.audio);
    } else {
      setCaptcha("", "");
    }
  };

  return {
    formikSlice,
    setFormik,
    setCaptcha,
    newCaptcha,
    resetGlobalFormik,
  };
};

export default useGlobalFormik;
