import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import PropTypes from "prop-types";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Tab Component
const Tab = ({ active, onClick, children, badge }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 rounded-lg font-medium transition-all relative ${
      active
        ? "bg-blue-600 text-white shadow-md"
        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
    }`}
  >
    {children}
    {badge > 0 && (
      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
        {badge}
      </span>
    )}
  </button>
);

Tab.propTypes = {
  active: PropTypes.bool,
  onClick: PropTypes.func,
  children: PropTypes.node,
  badge: PropTypes.number,
};

// Participant Card Component
const ParticipantCard = ({ participant, onInvite, inviteSent, loading, disabled }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow"
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="font-semibold text-gray-900">{participant.student_name}</h4>
        <p className="text-sm text-gray-500">{participant.student_id}</p>
        <div className="mt-2 flex flex-wrap gap-1">
          {participant.skills?.split(", ").slice(0, 3).map((skill, i) => (
            <span
              key={i}
              className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded-full"
            >
              {skill}
            </span>
          ))}
        </div>
        {participant.preferred_role && (
          <p className="text-xs text-gray-500 mt-2">
            Preferred: <span className="font-medium">{participant.preferred_role}</span>
          </p>
        )}
      </div>
      <button
        onClick={() => onInvite(participant.id)}
        disabled={inviteSent || loading || disabled}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
          inviteSent
            ? "bg-green-100 text-green-600 cursor-not-allowed"
            : disabled
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : loading
            ? "bg-gray-100 text-gray-400 cursor-wait"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {inviteSent ? "✓ Invited" : disabled ? "Locked" : loading ? "..." : "Invite"}
      </button>
    </div>
  </motion.div>
);

ParticipantCard.propTypes = {
  participant: PropTypes.object.isRequired,
  onInvite: PropTypes.func.isRequired,
  inviteSent: PropTypes.bool,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
};

// Team Card Component
const TeamCard = ({ team, onRequestJoin, onViewDetails, requestSent, loading, disabled }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow"
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="font-semibold text-gray-900">
          {team.team_name || `Team by ${team.creator_name}`}
        </h4>
        <p className="text-sm text-gray-500">
          {team.member_count}/{team.max_size} members
        </p>
        {/* Creator Info */}
        <div className="mt-2 p-2 bg-yellow-50 rounded-lg border border-yellow-100">
          <p className="text-xs text-yellow-700 font-medium flex items-center gap-1">
            <span>👑</span> Created by: {team.creator_name}
          </p>
          <p className="text-xs text-gray-500">{team.creator_id}</p>
          {team.creator_skills && (
            <div className="mt-1 flex flex-wrap gap-1">
              {team.creator_skills.split(", ").slice(0, 2).map((skill, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>
        {/* Quick member preview */}
        <div className="mt-2 flex flex-wrap gap-1">
          {team.members?.slice(0, 3).map((member, i) => (
            <span
              key={i}
              className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
            >
              {member.student_name}
            </span>
          ))}
          {team.members?.length > 3 && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
              +{team.members.length - 3} more
            </span>
          )}
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <button
          onClick={() => onViewDetails(team)}
          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
        >
          View Team
        </button>
        <button
          onClick={() => onRequestJoin(team.id)}
          disabled={requestSent || loading || !team.can_join || disabled}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            requestSent
              ? "bg-green-100 text-green-600 cursor-not-allowed"
              : disabled
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : !team.can_join
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : loading
              ? "bg-gray-100 text-gray-400 cursor-wait"
              : "bg-purple-600 text-white hover:bg-purple-700"
          }`}
        >
          {requestSent ? "✓ Requested" : disabled ? "Locked" : !team.can_join ? "Full" : loading ? "..." : "Join"}
        </button>
      </div>
    </div>
  </motion.div>
);

TeamCard.propTypes = {
  team: PropTypes.object.isRequired,
  onRequestJoin: PropTypes.func.isRequired,
  onViewDetails: PropTypes.func.isRequired,
  requestSent: PropTypes.bool,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
};

// Invitation Card Component
const InvitationCard = ({ invitation, type, onRespond, onCancel, loading, disabled }) => (
  <motion.div
    initial={{ opacity: 0, x: type === "received" ? -10 : 10 }}
    animate={{ opacity: 1, x: 0 }}
    className={`p-4 rounded-xl border ${
      type === "received"
        ? "bg-blue-50 border-blue-200"
        : "bg-gray-50 border-gray-200"
    }`}
  >
    <div className="flex items-start justify-between">
      <div>
        {type === "received" ? (
          <>
            <p className="font-medium text-gray-900">
              {invitation.sender_name} invited you
            </p>
            <p className="text-sm text-gray-600">
              to join &quot;{invitation.team_name || `Team by ${invitation.sender_name}`}&quot;
            </p>
          </>
        ) : (
          <>
            <p className="font-medium text-gray-900">
              Invitation to {invitation.recipient_name}
            </p>
            <p className="text-sm text-gray-600">Status: {invitation.status}</p>
          </>
        )}
        {invitation.message && (
          <p className="text-sm text-gray-500 mt-2 italic">
            &quot;{invitation.message}&quot;
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          {new Date(invitation.created_at).toLocaleDateString()}
        </p>
      </div>
      <div className="flex gap-2">
        {type === "received" && invitation.status === "pending" ? (
          disabled ? (
            <span className="px-3 py-1.5 bg-gray-100 text-gray-500 rounded-lg text-sm font-medium">
              🔒 Locked
            </span>
          ) : (
            <>
              <button
                onClick={() => onRespond(invitation.id, "accept")}
                disabled={loading}
                className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
              >
                Accept
              </button>
              <button
                onClick={() => onRespond(invitation.id, "decline")}
                disabled={loading}
                className="px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-sm font-medium hover:bg-red-200 disabled:opacity-50"
              >
                Decline
              </button>
            </>
          )
        ) : type === "sent" && invitation.status === "pending" ? (
          <button
            onClick={() => onCancel(invitation.id)}
            disabled={loading || disabled}
            className="px-3 py-1.5 bg-gray-200 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-300 disabled:opacity-50"
          >
            {disabled ? "🔒 Locked" : "Cancel"}
          </button>
        ) : (
          <span
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              invitation.status === "accepted"
                ? "bg-green-100 text-green-600"
                : invitation.status === "declined"
                ? "bg-red-100 text-red-600"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {invitation.status.charAt(0).toUpperCase() + invitation.status.slice(1)}
          </span>
        )}
      </div>
    </div>
  </motion.div>
);

InvitationCard.propTypes = {
  invitation: PropTypes.object.isRequired,
  type: PropTypes.oneOf(["sent", "received"]).isRequired,
  onRespond: PropTypes.func,
  onCancel: PropTypes.func,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
};

// Join Request Card Component
const JoinRequestCard = ({ request, type, onRespond, onCancel, loading, disabled }) => (
  <motion.div
    initial={{ opacity: 0, x: type === "received" ? -10 : 10 }}
    animate={{ opacity: 1, x: 0 }}
    className={`p-4 rounded-xl border ${
      type === "received"
        ? "bg-purple-50 border-purple-200"
        : "bg-gray-50 border-gray-200"
    }`}
  >
    <div className="flex items-start justify-between">
      <div>
        {type === "received" ? (
          <>
            <p className="font-medium text-gray-900">
              {request.requester_name} wants to join
            </p>
            <p className="text-sm text-gray-600">{request.requester_student_id}</p>
          </>
        ) : (
          <>
            <p className="font-medium text-gray-900">
              Request to join &quot;{request.team_name}&quot;
            </p>
            <p className="text-sm text-gray-600">Status: {request.status}</p>
          </>
        )}
        {request.message && (
          <p className="text-sm text-gray-500 mt-2 italic">
            &quot;{request.message}&quot;
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          {new Date(request.created_at).toLocaleDateString()}
        </p>
      </div>
      <div className="flex gap-2">
        {disabled ? (
          <span className="px-3 py-1.5 bg-gray-100 text-gray-500 rounded-lg text-sm font-medium">
            🔒 Locked
          </span>
        ) : type === "received" && request.status === "pending" ? (
          <>
            <button
              onClick={() => onRespond(request.id, "accept")}
              disabled={loading}
              className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
            >
              Accept
            </button>
            <button
              onClick={() => onRespond(request.id, "decline")}
              disabled={loading}
              className="px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-sm font-medium hover:bg-red-200 disabled:opacity-50"
            >
              Decline
            </button>
          </>
        ) : type === "sent" && request.status === "pending" ? (
          <button
            onClick={() => onCancel(request.id)}
            disabled={loading}
            className="px-3 py-1.5 bg-gray-200 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-300 disabled:opacity-50"
          >
            Cancel
          </button>
        ) : (
          <span
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              request.status === "accepted"
                ? "bg-green-100 text-green-600"
                : request.status === "declined"
                ? "bg-red-100 text-red-600"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
          </span>
        )}
      </div>
    </div>
  </motion.div>
);

JoinRequestCard.propTypes = {
  request: PropTypes.object.isRequired,
  type: PropTypes.oneOf(["sent", "received"]).isRequired,
  onRespond: PropTypes.func,
  onCancel: PropTypes.func,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
};

// My Team View Component
const MyTeamPanel = ({
  team,
  onLeave,
  onFinalize,
  onRemoveMember,
  loading,
  minSize,
  maxSize,
  isLocked,
}) => {
  if (!team) return null;

  const canFinalize = team.member_count >= minSize;
  const isFull = team.member_count >= maxSize;
  const hasOtherMembers = team.member_count > 1;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white rounded-2xl shadow-lg p-6"
    >
      {/* Locked Banner for team */}
      {isLocked && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-4">
          <p className="text-sm text-red-700 flex items-center gap-2">
            <span>🔒</span>
            <span>Team is locked. You cannot leave or modify the team.</span>
          </p>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">
            {team.team_name || "My Team"}
          </h3>
          <p className="text-gray-500">
            {team.member_count}/{maxSize} members
            {isFull && <span className="ml-2 text-green-600">(Full)</span>}
          </p>
        </div>
        {!isLocked && (
          <div className="flex gap-2">
            {team.is_creator && canFinalize && (
              <button
                onClick={onFinalize}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? "Finalizing..." : "Finalize Team"}
              </button>
            )}
            <button
              onClick={onLeave}
              disabled={loading}
              className="px-4 py-2 bg-red-100 text-red-600 rounded-lg font-medium hover:bg-red-200 disabled:opacity-50"
            >
              {team.is_creator && !hasOtherMembers ? "Disband Team" : "Leave Team"}
            </button>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Team Progress</span>
          <span className="text-gray-900 font-medium">
            {team.member_count} / {minSize} minimum
          </span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              canFinalize ? "bg-green-500" : "bg-blue-500"
            }`}
            style={{ width: `${Math.min((team.member_count / minSize) * 100, 100)}%` }}
          />
        </div>
        {!canFinalize && (
          <p className="text-sm text-orange-600 mt-1">
            Need {minSize - team.member_count} more member(s) to finalize
          </p>
        )}
      </div>

      {/* Team Members */}
      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900">Team Members</h4>
        {team.members?.map((member) => (
          <div
            key={member.id}
            className={`p-4 rounded-xl border ${
              member.is_creator 
                ? "bg-yellow-50 border-yellow-200" 
                : "bg-gray-50 border-gray-200"
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  member.is_creator 
                    ? "bg-yellow-200 text-yellow-700" 
                    : "bg-blue-100 text-blue-600"
                }`}>
                  {member.student_name?.charAt(0)}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">
                    {member.student_name}
                    {member.is_creator && (
                      <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                        👑 Creator
                      </span>
                    )}
                  </p>
                  <p className="text-sm text-gray-500">{member.student_id}</p>
                  {member.preferred_role && (
                    <p className="text-xs text-purple-600 mt-1">
                      Role: <span className="font-medium">{member.preferred_role}</span>
                    </p>
                  )}
                  {member.skills && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {member.skills.split(", ").map((skill, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              {team.is_creator && !member.is_creator && (
                <button
                  onClick={() => onRemoveMember(member.id)}
                  disabled={loading}
                  className="text-red-500 hover:text-red-700 disabled:opacity-50"
                  title="Remove member"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

MyTeamPanel.propTypes = {
  team: PropTypes.object,
  onLeave: PropTypes.func.isRequired,
  onFinalize: PropTypes.func.isRequired,
  onRemoveMember: PropTypes.func.isRequired,
  loading: PropTypes.bool,
  minSize: PropTypes.number,
  maxSize: PropTypes.number,
  isLocked: PropTypes.bool,
};

// Create Team Modal
const CreateTeamModal = ({ isOpen, onClose, onCreate, loading }) => {
  const [teamName, setTeamName] = useState("");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
      >
        <h3 className="text-xl font-bold text-gray-900 mb-4">Create a Team</h3>
        <input
          type="text"
          value={teamName}
          onChange={(e) => setTeamName(e.target.value)}
          placeholder="Team Name (optional)"
          className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-sm text-gray-500 mt-2">
          Leave blank for a default name based on your name
        </p>
        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onCreate(teamName)}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Team"}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

CreateTeamModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onCreate: PropTypes.func.isRequired,
  loading: PropTypes.bool,
};

// Team Details Modal - View team members and their skills
const TeamDetailsModal = ({ team, isOpen, onClose, onRequestJoin, requestSent, loading }) => {
  if (!isOpen || !team) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden"
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-purple-50 to-blue-50">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                {team.team_name || `Team by ${team.creator_name}`}
              </h3>
              <p className="text-gray-600 mt-1">
                {team.member_count}/{team.max_size} members • Min: {team.min_size}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/50 rounded-lg transition-colors"
            >
              <span className="text-xl">✕</span>
            </button>
          </div>
          
          {/* Creator Highlight */}
          <div className="mt-4 p-3 bg-white rounded-xl border border-yellow-200 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center text-yellow-600 font-bold text-lg">
                👑
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">
                  {team.creator_name}
                  <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                    Team Creator
                  </span>
                </p>
                <p className="text-sm text-gray-500">{team.creator_id}</p>
                {team.creator_skills && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {team.creator_skills.split(", ").map((skill, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-yellow-50 text-yellow-700 text-xs rounded-full border border-yellow-200"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Members List */}
        <div className="p-6 overflow-y-auto max-h-[45vh]">
          <h4 className="font-semibold text-gray-900 mb-4">
            Team Members ({team.members?.length || 0})
          </h4>
          <div className="space-y-3">
            {team.members?.map((member) => (
              <div
                key={member.id}
                className={`p-4 rounded-xl border ${
                  member.is_creator 
                    ? "bg-yellow-50 border-yellow-200" 
                    : "bg-gray-50 border-gray-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    member.is_creator 
                      ? "bg-yellow-200 text-yellow-700" 
                      : "bg-blue-100 text-blue-600"
                  }`}>
                    {member.student_name?.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900">{member.student_name}</p>
                      {member.is_creator && (
                        <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                          👑 Creator
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{member.student_id}</p>
                    {member.preferred_role && (
                      <p className="text-xs text-purple-600 mt-1">
                        Preferred Role: <span className="font-medium">{member.preferred_role}</span>
                      </p>
                    )}
                    {member.skills && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {member.skills.split(", ").map((skill, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-100 bg-gray-50">
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50"
            >
              Close
            </button>
            <button
              onClick={() => {
                onRequestJoin(team.id);
                onClose();
              }}
              disabled={requestSent || loading || !team.can_join}
              className={`flex-1 px-4 py-3 rounded-xl font-medium transition-all ${
                requestSent
                  ? "bg-green-100 text-green-600 cursor-not-allowed"
                  : !team.can_join
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : loading
                  ? "bg-gray-100 text-gray-400 cursor-wait"
                  : "bg-purple-600 text-white hover:bg-purple-700"
              }`}
            >
              {requestSent 
                ? "✓ Request Sent" 
                : !team.can_join 
                ? "Team Full" 
                : loading 
                ? "Sending..." 
                : "Request to Join Team"}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

TeamDetailsModal.propTypes = {
  team: PropTypes.object,
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onRequestJoin: PropTypes.func.isRequired,
  requestSent: PropTypes.bool,
  loading: PropTypes.bool,
};

// Main SelfGroupingView Component
const SelfGroupingView = ({ userData, eventData, onGroupFormed }) => {
  const [activeTab, setActiveTab] = useState("participants");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Data states
  const [status, setStatus] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [teams, setTeams] = useState([]);
  const [myTeam, setMyTeam] = useState(null);
  const [invitations, setInvitations] = useState({ sent: [], received: [] });
  const [joinRequests, setJoinRequests] = useState({ sent: [], received: [] });
  
  // UI states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTeamDetailsModal, setShowTeamDetailsModal] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [invitedParticipants, setInvitedParticipants] = useState(new Set());
  const [requestedTeams, setRequestedTeams] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState("");

  const accessKey = localStorage.getItem("cq_access_key") || sessionStorage.getItem("cq_access_key");

  // Handler to view team details
  const handleViewTeamDetails = (team) => {
    setSelectedTeam(team);
    setShowTeamDetailsModal(true);
  };

  // Fetch self-grouping status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/codequest/self-grouping/status/?access_key=${accessKey}`
      );
      setStatus(response.data);
      return response.data;
    } catch (err) {
      console.error("Failed to fetch status:", err);
      setError(err.response?.data?.error || "Failed to load status");
    }
  }, [accessKey]);

  // Fetch available participants
  const fetchParticipants = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/codequest/self-grouping/participants/?access_key=${accessKey}`
      );
      setParticipants(response.data.participants || []);
    } catch (err) {
      console.error("Failed to fetch participants:", err);
    }
  }, [accessKey]);

  // Fetch available teams (excludes user's team - also filtered on backend)
  const fetchTeams = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/codequest/self-grouping/teams/?access_key=${accessKey}`
      );
      // Backend already excludes user's teams, but filter here too as backup
      const teamsData = response.data.teams || [];
      setTeams(teamsData);
    } catch (err) {
      console.error("Failed to fetch teams:", err);
    }
  }, [accessKey]);

  // Fetch my team
  const fetchMyTeam = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/codequest/self-grouping/my-team/?access_key=${accessKey}`
      );
      setMyTeam(response.data.team);
    } catch (err) {
      if (err.response?.status !== 404) {
        console.error("Failed to fetch my team:", err);
      }
      setMyTeam(null);
    }
  }, [accessKey]);

  // Fetch invitations
  const fetchInvitations = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/codequest/self-grouping/invitations/?access_key=${accessKey}`
      );
      setInvitations({
        sent: response.data.sent || [],
        received: response.data.received || [],
      });
    } catch (err) {
      console.error("Failed to fetch invitations:", err);
    }
  }, [accessKey]);

  // Fetch join requests
  const fetchJoinRequests = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/codequest/self-grouping/join-requests/?access_key=${accessKey}`
      );
      setJoinRequests({
        sent: response.data.sent || [],
        received: response.data.received || [],
      });
    } catch (err) {
      console.error("Failed to fetch join requests:", err);
    }
  }, [accessKey]);

  // Load all data
  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      const statusData = await fetchStatus();
      
      if (statusData?.self_grouping_enabled) {
        await Promise.all([
          fetchParticipants(),
          fetchTeams(),
          fetchMyTeam(),
          fetchInvitations(),
          fetchJoinRequests(),
        ]);
      }
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  }, [fetchStatus, fetchParticipants, fetchTeams, fetchMyTeam, fetchInvitations, fetchJoinRequests]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Update invited participants set from invitations
  useEffect(() => {
    const invited = new Set(
      invitations.sent
        .filter((inv) => inv.status === "pending")
        .map((inv) => inv.recipient_id)
    );
    setInvitedParticipants(invited);
  }, [invitations.sent]);

  // Update requested teams set from join requests
  useEffect(() => {
    const requested = new Set(
      joinRequests.sent
        .filter((req) => req.status === "pending")
        .map((req) => req.team_id)
    );
    setRequestedTeams(requested);
  }, [joinRequests.sent]);

  // Create team handler
  const handleCreateTeam = async (teamName) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/create-team/?access_key=${accessKey}`,
        { team_name: teamName }
      );
      setShowCreateModal(false);
      await loadAllData();
      setActiveTab("myteam");
    } catch (err) {
      alert(err.response?.data?.error || "Failed to create team");
    } finally {
      setActionLoading(false);
    }
  };

  // Send invitation handler
  const handleInvite = async (participantId) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/invite/?access_key=${accessKey}`,
        { recipient_id: participantId }
      );
      setInvitedParticipants((prev) => new Set([...prev, participantId]));
      await fetchInvitations();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to send invitation");
    } finally {
      setActionLoading(false);
    }
  };

  // Cancel invitation handler
  const handleCancelInvitation = async (invitationId) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/invite/${invitationId}/cancel/?access_key=${accessKey}`,
        {}
      );
      await fetchInvitations();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to cancel invitation");
    } finally {
      setActionLoading(false);
    }
  };

  // Respond to invitation handler
  const handleRespondToInvitation = async (invitationId, action) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/invite/${invitationId}/respond/?access_key=${accessKey}`,
        { action }
      );
      await loadAllData();
      if (action === "accept") {
        setActiveTab("myteam");
      }
    } catch (err) {
      alert(err.response?.data?.error || "Failed to respond to invitation");
    } finally {
      setActionLoading(false);
    }
  };

  // Send join request handler
  const handleRequestJoin = async (teamId) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/request-join/?access_key=${accessKey}`,
        { team_id: teamId }
      );
      setRequestedTeams((prev) => new Set([...prev, teamId]));
      await fetchJoinRequests();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to send join request");
    } finally {
      setActionLoading(false);
    }
  };

  // Cancel join request handler
  const handleCancelJoinRequest = async (requestId) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/request/${requestId}/cancel/?access_key=${accessKey}`,
        {}
      );
      await fetchJoinRequests();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to cancel request");
    } finally {
      setActionLoading(false);
    }
  };

  // Respond to join request handler
  const handleRespondToJoinRequest = async (requestId, action) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/request/${requestId}/respond/?access_key=${accessKey}`,
        { action }
      );
      await loadAllData();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to respond to request");
    } finally {
      setActionLoading(false);
    }
  };

  // Leave team handler
  const handleLeaveTeam = async () => {
    const hasOtherMembers = myTeam?.member_count > 1;
    let confirmMessage;
    
    if (myTeam?.is_creator) {
      if (hasOtherMembers) {
        confirmMessage = "If you leave, the next team member will become the new creator. Are you sure you want to leave?";
      } else {
        confirmMessage = "You are the only member. If you leave, the team will be disbanded. Are you sure?";
      }
    } else {
      confirmMessage = "Are you sure you want to leave this team?";
    }
    
    if (!confirm(confirmMessage)) {
      return;
    }
    setActionLoading(true);
    try {
      const response = await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/leave-team/?access_key=${accessKey}`,
        {}
      );
      // Show feedback if there's a new creator
      if (response.data.new_creator) {
        alert(`You have left the team. ${response.data.new_creator} is now the team creator.`);
      }
      await loadAllData();
      setActiveTab("participants");
    } catch (err) {
      alert(err.response?.data?.error || "Failed to leave team");
    } finally {
      setActionLoading(false);
    }
  };

  // Finalize team handler
  const handleFinalizeTeam = async () => {
    if (!confirm("Are you sure you want to finalize this team? This action cannot be undone and will create your official group.")) {
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/codequest/self-grouping/finalize/?access_key=${accessKey}`,
        {}
      );
      // Notify parent that group was formed
      if (onGroupFormed) {
        onGroupFormed();
      }
    } catch (err) {
      alert(err.response?.data?.error || "Failed to finalize team");
    } finally {
      setActionLoading(false);
    }
  };

  // Remove member handler (for team creator)
  const handleRemoveMember = async (memberId) => {
    if (!confirm("Are you sure you want to remove this member?")) {
      return;
    }
    // This would need an endpoint - leaving as placeholder
    console.log("Remove member:", memberId);
  };

  // Filter participants by search
  const filteredParticipants = participants.filter(
    (p) =>
      p.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.student_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.skills?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Count pending items for badges
  const pendingReceivedInvitations = invitations.received.filter(
    (inv) => inv.status === "pending"
  ).length;
  const pendingReceivedRequests = joinRequests.received.filter(
    (req) => req.status === "pending"
  ).length;

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading self-grouping...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="text-6xl mb-4">😕</div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={loadAllData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!status?.self_grouping_enabled) {
    return (
      <div className="p-6 text-center">
        <div className="text-6xl mb-4">🚫</div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Self-Grouping Not Available
        </h3>
        <p className="text-gray-600">
          Self-grouping is not enabled for this event. Please wait for the admin
          to form groups.
        </p>
      </div>
    );
  }

  // Check if self-grouping has not started yet
  if (status?.self_grouping_status === 'not_started') {
    return (
      <div className="p-6 text-center">
        <div className="text-6xl mb-4">⏳</div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Self-Grouping Coming Soon
        </h3>
        <p className="text-gray-600 mb-4">
          Self-grouping has not started yet. Please wait until the scheduled start time.
        </p>
        {status?.start_date && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 inline-block">
            <p className="text-sm text-blue-700">
              <span className="font-medium">Starts:</span>{" "}
              {new Date(status.start_date).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    );
  }

  // Check if self-grouping is locked (ended)
  const isLocked = status?.is_locked || status?.self_grouping_status === 'locked';

  return (
    <div className="p-6">
      {/* Lockdown Banner */}
      {isLocked && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🔒</span>
            <div>
              <p className="font-medium text-red-900">Self-Grouping Period Has Ended</p>
              <p className="text-sm text-red-700 mt-1">
                Teams are now locked. You cannot create, join, or leave teams.
                {status?.end_date && (
                  <span className="block mt-1">
                    Ended: {new Date(status.end_date).toLocaleString()}
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
           
            {userData && (
              <p className="text-sm text-gray-500 mt-1">
                Logged in as <span className="font-medium">{userData.student_name}</span> ({userData.student_id})
              </p>
            )}
          </div>
          {!myTeam && !isLocked && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              + Create Team
            </button>
          )}
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="font-medium text-blue-900">How Self-Grouping Works</p>
              <ul className="text-sm text-blue-700 mt-1 space-y-1">
                <li>• Create a team or join an existing one</li>
                <li>• Invite participants or request to join teams</li>
                <li>• Teams need {status?.min_group_size || eventData?.min_group_size || 5}-{status?.max_group_size || eventData?.max_group_size || 7} members</li>
                <li>• Team creator can finalize when minimum members are met</li>
                {status?.end_date && !isLocked && (
                  <li className="text-orange-600 font-medium">
                    ⚠️ Self-grouping ends: {new Date(status.end_date).toLocaleString()}
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 flex-wrap">
          <Tab
            active={activeTab === "participants"}
            onClick={() => setActiveTab("participants")}
          >
            Find Participants
          </Tab>
          <Tab
            active={activeTab === "teams"}
            onClick={() => setActiveTab("teams")}
          >
            Browse Teams
          </Tab>
          <Tab
            active={activeTab === "invitations"}
            onClick={() => setActiveTab("invitations")}
            badge={pendingReceivedInvitations}
          >
            Invitations
          </Tab>
          <Tab
            active={activeTab === "requests"}
            onClick={() => setActiveTab("requests")}
            badge={pendingReceivedRequests}
          >
            Join Requests
          </Tab>
          {myTeam && (
            <Tab
              active={activeTab === "myteam"}
              onClick={() => setActiveTab("myteam")}
            >
              My Team
            </Tab>
          )}
        </div>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === "participants" && (
          <motion.div
            key="participants"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {/* Search */}
            <div className="mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name, ID, or skills..."
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {!myTeam && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-4">
                <p className="text-yellow-800">
                  ⚠️ Create a team first to invite participants
                </p>
              </div>
            )}

            {filteredParticipants.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-xl">
                <div className="text-4xl mb-2">👥</div>
                <p className="text-gray-600">No available participants found</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredParticipants.map((participant) => (
                  <ParticipantCard
                    key={participant.id}
                    participant={participant}
                    onInvite={handleInvite}
                    inviteSent={invitedParticipants.has(participant.id)}
                    loading={actionLoading}
                    disabled={isLocked}
                  />
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === "teams" && (
          <motion.div
            key="teams"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {teams.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-xl">
                <div className="text-4xl mb-2">{myTeam ? "✅" : "🏠"}</div>
                {myTeam ? (
                  <>
                    <p className="text-gray-600 mb-2">No other teams available to browse</p>
                    <p className="text-sm text-gray-500">
                      You&apos;re already part of a team. Check the &quot;My Team&quot; tab to view your team.
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-gray-600 mb-4">No teams available to join</p>
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg"
                    >
                      Create Your Own Team
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {teams.map((team) => (
                  <TeamCard
                    key={team.id}
                    team={team}
                    onRequestJoin={handleRequestJoin}
                    onViewDetails={handleViewTeamDetails}
                    requestSent={requestedTeams.has(team.id)}
                    loading={actionLoading}
                    disabled={isLocked}
                  />
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === "invitations" && (
          <motion.div
            key="invitations"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Received Invitations */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">
                Received Invitations ({invitations.received.length})
              </h3>
              {invitations.received.length === 0 ? (
                <p className="text-gray-500 text-center py-6 bg-gray-50 rounded-xl">
                  No invitations received
                </p>
              ) : (
                <div className="space-y-3">
                  {invitations.received.map((invitation) => (
                    <InvitationCard
                      key={invitation.id}
                      invitation={invitation}
                      type="received"
                      onRespond={handleRespondToInvitation}
                      loading={actionLoading}
                      disabled={isLocked}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Sent Invitations */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">
                Sent Invitations ({invitations.sent.length})
              </h3>
              {invitations.sent.length === 0 ? (
                <p className="text-gray-500 text-center py-6 bg-gray-50 rounded-xl">
                  No invitations sent
                </p>
              ) : (
                <div className="space-y-3">
                  {invitations.sent.map((invitation) => (
                    <InvitationCard
                      key={invitation.id}
                      invitation={invitation}
                      type="sent"
                      onCancel={handleCancelInvitation}
                      loading={actionLoading}
                      disabled={isLocked}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === "requests" && (
          <motion.div
            key="requests"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Received Requests (for team creators) */}
            {myTeam?.is_creator && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">
                  Requests to Join Your Team ({joinRequests.received.length})
                </h3>
                {joinRequests.received.length === 0 ? (
                  <p className="text-gray-500 text-center py-6 bg-gray-50 rounded-xl">
                    No join requests received
                  </p>
                ) : (
                  <div className="space-y-3">
                    {joinRequests.received.map((request) => (
                      <JoinRequestCard
                        key={request.id}
                        request={request}
                        type="received"
                        onRespond={handleRespondToJoinRequest}
                        loading={actionLoading}
                        disabled={isLocked}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Sent Requests */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">
                Your Join Requests ({joinRequests.sent.length})
              </h3>
              {joinRequests.sent.length === 0 ? (
                <p className="text-gray-500 text-center py-6 bg-gray-50 rounded-xl">
                  No join requests sent
                </p>
              ) : (
                <div className="space-y-3">
                  {joinRequests.sent.map((request) => (
                    <JoinRequestCard
                      key={request.id}
                      request={request}
                      type="sent"
                      onCancel={handleCancelJoinRequest}
                      loading={actionLoading}
                      disabled={isLocked}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === "myteam" && myTeam && (
          <motion.div
            key="myteam"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <MyTeamPanel
              team={myTeam}
              onLeave={handleLeaveTeam}
              onFinalize={handleFinalizeTeam}
              onRemoveMember={handleRemoveMember}
              loading={actionLoading}
              minSize={status?.min_group_size || eventData?.min_group_size || 5}
              maxSize={status?.max_group_size || eventData?.max_group_size || 7}
              isLocked={isLocked}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Team Modal */}
      <CreateTeamModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateTeam}
        loading={actionLoading}
      />

      {/* Team Details Modal */}
      <TeamDetailsModal
        team={selectedTeam}
        isOpen={showTeamDetailsModal}
        onClose={() => {
          setShowTeamDetailsModal(false);
          setSelectedTeam(null);
        }}
        onRequestJoin={handleRequestJoin}
        requestSent={selectedTeam ? requestedTeams.has(selectedTeam.id) : false}
        loading={actionLoading}
      />
    </div>
  );
};

SelfGroupingView.propTypes = {
  userData: PropTypes.object,
  eventData: PropTypes.object,
  onGroupFormed: PropTypes.func,
};

export default SelfGroupingView;
