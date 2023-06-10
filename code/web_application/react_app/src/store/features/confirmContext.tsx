import React, { createContext, useState } from "react";

// * Confirm as context because Redux does not support functions

interface AppContextInterface {
  title: string;
  desc: string;
  confirm?: () => void;
  unconfirm?: () => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export const ConfirmContext = createContext<{
  confirm: AppContextInterface | null;
  setConfirm: React.Dispatch<React.SetStateAction<AppContextInterface>> | null;
}>({ confirm: null, setConfirm: null });

const initalState: AppContextInterface = {
  title: "",
  desc: "",
};

interface AppProps {
  children: React.ReactNode;
}

const ConfirmContextProvider = ({ children }: AppProps) => {
  const [confirm, setConfirm] = useState<AppContextInterface>(initalState);
  return (
    <ConfirmContext.Provider value={{ confirm, setConfirm }}>
      {children}
    </ConfirmContext.Provider>
  );
};

export default ConfirmContextProvider;
