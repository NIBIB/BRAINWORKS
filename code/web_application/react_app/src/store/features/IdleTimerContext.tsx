import React, { createContext, useState } from "react";
import { IIdleTimer } from "react-idle-timer";

// * Confirm as context because Redux does not support functions

export const IdleTimerContext = createContext<{
  idleTimer: IIdleTimer | null;
  setIdleTimer: React.Dispatch<React.SetStateAction<IIdleTimer | null>> | null;
}>({ idleTimer: null, setIdleTimer: null });

interface AppProps {
  children: React.ReactNode;
}

const IdleTimerContextProvider = ({ children }: AppProps) => {
  const [idleTimer, setIdleTimer] = useState<IIdleTimer | null>(null);
  return (
    <IdleTimerContext.Provider value={{ idleTimer, setIdleTimer }}>
      {children}
    </IdleTimerContext.Provider>
  );
};

export default IdleTimerContextProvider;
