import { motion } from "framer-motion";
import { User, UserCheck, GraduationCap, Building } from "lucide-react";

export function UserTypeStep({ formData, onInputChange, onStudentLoginRequired }) {
  const handleUserTypeChange = (type) => {
    onInputChange({ target: { name: 'is_student', value: type } });
    
    // If student type is selected, trigger login requirement
    if (type === 'student' && onStudentLoginRequired) {
      onStudentLoginRequired();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to El Mercado Seller Application
        </h1>
        <p className="text-lg text-gray-600">
          Let's start by understanding who you are
        </p>
      </div>

      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Are you a current Computer Science OR Information Technology Student?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Student Option */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleUserTypeChange('student')}
            className={`relative p-6 rounded-xl border-2 cursor-pointer transition-all ${
              formData.is_student === 'student'
                ? 'border-blue-500 bg-blue-50 shadow-lg'
                : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
            }`}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className={`p-4 rounded-full ${
                formData.is_student === 'student' ? 'bg-blue-100' : 'bg-gray-100'
              }`}>
                <GraduationCap className={`w-8 h-8 ${
                  formData.is_student === 'student' ? 'text-blue-600' : 'text-gray-600'
                }`} />
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Yes, I'm a CSS Student
                </h3>
                <p className="text-sm text-gray-600">
                  I have a student account and want to sell items or services to fellow students
                </p>
              </div>

              <div className={`mt-4 px-4 py-2 rounded-full text-xs font-medium ${
                formData.is_student === 'student' 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                Login Required
              </div>
            </div>

            {formData.is_student === 'student' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-2 -right-2 bg-blue-500 text-white rounded-full p-1"
              >
                <UserCheck className="w-4 h-4" />
              </motion.div>
            )}
          </motion.div>

          {/* Non-Student Option */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleUserTypeChange('non-student')}
            className={`relative p-6 rounded-xl border-2 cursor-pointer transition-all ${
              formData.is_student === 'non-student'
                ? 'border-green-500 bg-green-50 shadow-lg'
                : 'border-gray-200 hover:border-green-300 hover:shadow-md'
            }`}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className={`p-4 rounded-full ${
                formData.is_student === 'non-student' ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                <Building className={`w-8 h-8 ${
                  formData.is_student === 'non-student' ? 'text-green-600' : 'text-gray-600'
                }`} />
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No, I'm Not a Student
                </h3>
                <p className="text-sm text-gray-600">
                  I'm a business owner, alumni, or community member wanting to sell on the platform
                </p>
              </div>

              <div className={`mt-4 px-4 py-2 rounded-full text-xs font-medium ${
                formData.is_student === 'non-student' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                No Login Required
              </div>
            </div>

            {formData.is_student === 'non-student' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1"
              >
                <UserCheck className="w-4 h-4" />
              </motion.div>
            )}
          </motion.div>
        </div>

        {/* Additional Information */}
        {formData.is_student && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-6 p-4 rounded-lg bg-gray-50 border border-gray-200"
          >
            {formData.is_student === 'student' ? (
              <div className="flex items-start space-x-3">
                <div className="bg-blue-100 p-2 rounded-full mt-1">
                  <User className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Student Account Benefits</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    As a student, your account will be linked to your student profile. This helps build trust 
                    with other students and provides access to student-exclusive features and categories.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-start space-x-3">
                <div className="bg-green-100 p-2 rounded-full mt-1">
                  <Building className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">External Seller Application</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    You'll be able to apply without creating a student account. We'll provide you with a 
                    tracking code to check your application status and access your seller portal once approved.
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}