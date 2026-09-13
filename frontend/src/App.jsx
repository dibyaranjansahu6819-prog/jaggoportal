import {
    BrowserRouter,
    Routes,
    Route,
    Navigate,
} from "react-router-dom";

import TeacherSignup from "./pages/TeacherSignup";
import StudentSignup from "./pages/StudentSignup";


function App() {

    return (

        <BrowserRouter>

            <Routes>

                {/* Default page */}
                <Route
                    path="/"
                    element={
                        <Navigate
                            to="/teacher/signup"
                            replace
                        />
                    }
                />

                {/* Teacher Registration */}
                <Route
                    path="/teacher/signup"
                    element={<TeacherSignup />}
                />

                {/* Student Registration */}
                <Route
                    path="/student/signup"
                    element={<StudentSignup />}
                />

            </Routes>

        </BrowserRouter>

    );

}


export default App;