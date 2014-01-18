#!/opt/local/bin/python

## For anything
from twisted.internet import reactor

## For WebSockets
try:
	## New style autobahn
	from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS
except ImportError:
	## Old style autobahn
	from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS

## All payloads are JSON-formatted.
import json
from chain_computer import *
from tictoc import tic, toc, tictoc_dec
from itertools import izip as zip
from numpy import argmax

kVerbose = 2
kStubOnly = False

class WebGUIServerProtocol( WebSocketServerProtocol ):
	def connectionMade( self ):
		WebSocketServerProtocol.connectionMade( self )
		self.engine = self.factory.engine
		
		print 'CONNECTED'
	
	@tictoc_dec
	def onMessage( self, msg, binary ):
		### BEGIN DEBUGGING
		if kVerbose >= 2:
			if not binary:
				from pprint import pprint
				space = msg.find( ' ' )
				if space == -1:
					print msg
				else:
					print msg[ :space ]
					pprint( json.loads( msg[ space+1 : ] ) )
		elif kVerbose >= 1:
			if not binary:
				print msg[:72] + ( ' ...' if len( msg ) > 72 else '' )
		### END DEBUGGING
		if kStubOnly: return
		
		if binary:
			print 'Received unknown message: binary of length', len( msg )
		
		elif msg.startswith( 'paths-info ' ):	   
			paths_info = json.loads( msg[ len( 'paths-info ' ): ] )
			try:
				boundary_index = argmax([ info['bbox_area'] for info in paths_info if info['closed'] ])
			except ValueError:
				boundary_index = -1
			
			self.engine.set_control_positions( paths_info, boundary_index )
			all_constraints = self.engine.all_constraints

			for i, constraints in enumerate( all_constraints ):
				for j, constraint in enumerate( constraints ):
	
					continuity = constraint[0]
					fixed = constraint[1]
					
					payload = [ i, j, { 'fixed': fixed, 'continuity': continuity} ]
					self.sendMessage( 'control-point-constraint ' + json.dumps( payload ) )

		
		elif msg.startswith( 'handle-positions-and-transforms ' ):
			handles = json.loads( msg[ len( 'handle-positions-and-transforms ' ): ] )
			
			positions = [ pos for pos, transform in handles ]
			transforms = [ transform for pos, transform in handles ]
			self.engine.set_handle_positions( positions, transforms )
			## Stop here it if it's empty.
			if len( handles ) == 0: return
			
			self.engine.precompute_configuration()
			self.engine.prepare_to_solve()
			
			all_paths = self.engine.solve_transform_change()

			all_positions = make_chain_from_control_groups( all_paths )
			self.sendMessage( 'paths-positions ' + json.dumps( all_positions ) )

			## Generate the triangulation and the BBW weights.
			# self.engine ...
		
		elif msg.startswith( 'handle-transforms ' ):
			handle_transforms = json.loads( msg[ len( 'handle-transforms ' ): ] )
			
			tic( 'transform_change' )
			for handle_index, handle_transform in handle_transforms:
				self.engine.transform_change( handle_index, handle_transform )
			toc()
			
			tic( 'engine.solve()' )
			all_paths = self.engine.solve_transform_change()	
#			debugger()
			toc()

			tic( 'make_chain_from_control_groups' )
			all_positions = make_chain_from_control_groups( all_paths )
			toc()
			self.sendMessage( 'paths-positions ' + json.dumps( all_positions ) )

			## Solve for the new curve positions given the updated transform matrix.
			# new_positions = engine ...
			
			## Send the new positions to the GUI.
			# self.sendMessage( 'paths-positions ' + json.dumps( new_positions ) )
		
		elif msg.startswith( 'control-point-constraint ' ):
			paths_info = json.loads( msg[ len( 'control-point-constraint ' ): ] )
			
			constraint = [None]*2
			constraint[0] = str( paths_info[2][ u'continuity' ] )
			constraint[1] = paths_info[2][ u'fixed' ]
			
			self.engine.constraint_change( paths_info[0], paths_info[1], constraint )
			
			try:
				self.engine.prepare_to_solve()
				all_paths = self.engine.solve_transform_change()
	
				all_positions = make_chain_from_control_groups( all_paths )
				self.sendMessage( 'paths-positions ' + json.dumps( all_positions ) )
			
			except NoHandlesError:
				## No handles yet, so nothing to do.
				pass

			## Solve for the new curve positions given the updated control point constraint.
			# new_positions = self.engine ...
			
			## Send the new positions to the GUI.
			# self.sendMessage( json.dumps( new_positions ) )
		
		elif msg.startswith( 'set-weight-function ' ):
			weight_function = json.loads( msg[ len( 'set-weight-function ' ): ] )
			
			## Do nothing if this would do nothing.
			if self.engine.get_weight_function() == weight_function: return
			
			self.engine.set_weight_function( weight_function )
			
			try:
				self.engine.prepare_to_solve()
				all_paths = self.engine.solve_transform_change()
				all_positions = make_chain_from_control_groups( all_paths )
				self.sendMessage( 'paths-positions ' + json.dumps( all_positions ) )
				self.retrieve_energy()
				
			except NoHandlesError:
				## No handles yet, so nothing to do.
				pass
		
		elif msg.startswith( 'enable-arc-length ' ):
			enable_arc_length = json.loads( msg[ len( 'enable-arc-length ' ): ] )
			
			## Do nothing if this would do nothing.
			if self.engine.get_enable_arc_length() == enable_arc_length: return
			
			self.engine.set_enable_arc_length( enable_arc_length )
			
			try:
				self.engine.prepare_to_solve()
				all_paths = self.engine.solve_transform_change()
				all_positions = make_chain_from_control_groups( all_paths )
				self.sendMessage( 'paths-positions ' + json.dumps( all_positions ) )
				self.retrieve_energy()
				
			except NoHandlesError:
				## No handles yet, so nothing to do.
				pass
				
		elif msg.startswith( 'handle-transform-drag-finished' ):
			
			self.retrieve_energy()
			
		else:
			print 'Received unknown message:', msg
			
	def retrieve_energy( self )	:
	
		energy, polylines = self.engine.compute_energy()
		
		energy_and_polyline = [
			[
				{ 'target-curve-polyline': points.tolist(), 'energy': energy }
				for energy, points in zip( path_energy, path_points )
			]
			for path_energy, path_points in zip( energy, polylines )
			]
		
		
		self.sendMessage( 'update-target-curve ' + json.dumps( energy_and_polyline ) )

def make_chain_from_control_groups( all_paths ):
	
	all_positions = []	
	for path in all_paths:
		if len( path ) > 1:
			new_positions = concatenate( asarray(path)[:-1, :-1] )
			new_positions = concatenate( ( new_positions, path[-1] ) )
		else:
			new_positions = path[0]
		new_positions = new_positions.tolist()
		all_positions.append( new_positions )
		
	return all_positions


def setupWebSocket( address, engine ):
	'''
	Listen for WebSocket connections at the given address.
	'''
	
	factory = WebSocketServerFactory( address )
	factory.engine = engine
	factory.protocol = WebGUIServerProtocol
	listenWS( factory )
	
	print "Listening for WebSocket connections at:", address

if __name__ == '__main__':
	import os, sys
	
	if 'stub' in sys.argv[1:]:
		kStubOnly = True
	
	if 'verbose' in sys.argv[1:]:
		kVerbose = int( sys.argv[ sys.argv.index( 'verbose' ) + 1 ] )
	
	print 'Verbosity level:', kVerbose
	print 'Stub only:', kStubOnly
	
	## Create engine:
	# engine = ...
	engine = Engine()
	
	setupWebSocket( "ws://localhost:9123", engine )
	
	## Maybe you find this convenient
	if 'open' in sys.argv[1:]:
		os.system( 'open web-gui.html' )
	
	reactor.run()
