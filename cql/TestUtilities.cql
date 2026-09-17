library "TestUtilities" version '1.0.0'

define function TestFailure(label String, message String):
  Message(false, true, '300', 'Error', label + ': ' + message)

define function SimpleTestFailure(label String):
  TestFailure(label, 'Actual value is not equal to expected value')
