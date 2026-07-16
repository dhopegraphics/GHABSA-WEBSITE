const MyGroupView = ({ groupData, userData }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Group Header */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {groupData?.group_name || "Your Group"}
            </h2>
            <p className="text-gray-600 mt-1">
              Group {groupData?.group_number || ""}
            </p>
          </div>
          <div className="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium">
            {groupData?.members?.length || 0} Members
          </div>
        </div>

        {/* Consultant Info */}
        {groupData?.consultant && (
          <div className="bg-blue-50 rounded-lg p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
              {groupData.consultant.name?.charAt(0) || "C"}
            </div>
            <div>
              <p className="text-sm text-gray-600">Consultant</p>
              <p className="font-semibold text-gray-900">
                {groupData.consultant.name}
              </p>
              <p className="text-sm text-gray-600">
                {groupData.consultant.expertise}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Project Manager */}
      {groupData?.project_manager && (
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-xl shadow-md p-6">
          <div className="flex items-center gap-4">
            <span className="text-4xl">⭐</span>
            <div>
              <p className="text-sm text-gray-600">Project Manager</p>
              <p className="text-xl font-bold text-gray-900">
                {groupData.project_manager.name}
              </p>
              <p className="text-sm text-gray-600">
                {groupData.project_manager.student_id}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Team Members */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          Team Members ({groupData?.members?.length || 0})
        </h3>
        <div className="space-y-3">
          {groupData?.members?.map((member, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-2 transition-all ${
                member.student_id === userData?.student_id
                  ? "border-blue-300 bg-blue-50"
                  : "border-gray-200 bg-gray-50"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                    {member.name?.charAt(0) || "M"}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      {member.name}
                      {member.student_id === userData?.student_id && (
                        <span className="ml-2 text-blue-600 text-sm">
                          (You)
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-gray-600">{member.student_id}</p>
                  </div>
                </div>
                <div className="text-right">
                  {member.role ? (
                    <div>
                      <p className="font-medium text-gray-900">{member.role}</p>
                      {member.is_lead && (
                        <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">
                          Lead
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-sm text-gray-500">
                      Role not assigned
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MyGroupView;
