import { RouteSectionProps } from '@solidjs/router';
import type { Component } from 'solid-js';

const App: Component<RouteSectionProps<unknown>> = props => {
  return (
    <>
    <h1>My Site with lots of pages</h1>
    {props.children}
    </>
  );
};

export default App;
